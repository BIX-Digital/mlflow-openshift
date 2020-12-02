import requests
import time
import logging
import yaml
import datetime

import openshift as oc
from openshift.model import OpenShiftPythonException

from mlflow.exceptions import MlflowException

from mlflow_openshift.defaults import RUNNING_STATUS, TERMINATED_STATUS, \
    WAITING_STATUS

from .defaults import RETRIES, SLEEP_TIME


logger = logging.getLogger(__name__)


def get_project_name():
    """Returns the current openshift project

    Returns:
        str: name of openshift project
    """
    return oc.get_project_name()


def apply_deployment_config(config, template):
    """Applies given arguments to openshift template and deploys it.

    Args:
        param_string (str): contains string representation of openshift parameters,
            e.g. --param=NAME=<some-name>
        template (str): filepath to openshift deployment template yaml.
    """
    with open("mlflow_openshift/templates/deploy_with_auth.yml") as f:
        template_dict = yaml.safe_load(f)
    template_obj = oc.APIObject(template_dict)

    processed_template = template_obj.process(parameters=config)
    oc.apply(processed_template)


def get_raw_pod_info(name):
    """Gets full pod information json

    Args:
        name (str): name of application

    Returns:
        str: pod information encoded in json
    """
    try:
        pod_info = oc.selector("pods", labels={"app": name}).object().as_json()
    except OpenShiftPythonException:
        pod_info = None
    return pod_info


def update_container_image(dc_obj, config):
    """Patches deployment config of an already existing mlflow deployment
    with a new configuration, i.e. docker image, tag.

    Args:
        dc_obj (openshift.apiobject.APIOoject): containing the deployment config
            of the already deployed mlflow model pod.
        model_uri (str): path where to find the mlflow packed model


    Returns:
        openshift.apiobject.APIOoject: containing the patched deployment config
    """
    new_image = config["docker_registry"] + "/" + config["image"] + ":" + config["tag"]
    dc_obj.model.spec.template.spec.containers[1].image = new_image
    return dc_obj


def update_model_uri(dc_obj, model_uri):
    """Patches deployment config of an already existing mlflow deployment
    with a new model-uri.

    Args:
        dc_obj (openshift.apiobject.APIOoject): containing the deployment config
            of the already deployed mlflow model pod.
        model_uri (str): path where to find the mlflow packed model


    Returns:
        openshift.apiobject.APIOoject: containing the patched deployment config
    """
    command = dc_obj.model.spec.template.spec.containers[1].command
    command[4] = model_uri
    dc_obj.model.spec.template.spec.containers[1].command = command
    return dc_obj


def delete_all_resources(name, project):
    """Deletes all resources (dc, routes, etc.) for the given name and project

    Args:
        name (str): application name
        project (str): openshift project name
    """
    oc.selector(labels={"app": name}).delete()


def check_succesful_deployment(name, route_host, auth_user, auth_password):
    """Checks if the deployed model endpoint has been started correctly.

    Args:
        name (str): name of the openshift application
        route_host (str): url of the model endpoint
        auth_user (str): username for the route
        auth_password (str): password for the route

    Notes:
        Currently able to catch two different dpeloyment errors.
        Container start up errors, e.g. wrong model name and image pulling
        errors, e.g. image name does not exist

    Raises:
        MlflowException: Generic container start error
        MlflowException: Image pulling error
    """
    time.sleep(SLEEP_TIME)
    check_completed = False

    while not check_completed:
        pod_obj = get_pod_info_from_app_name(name)
        try:
            container_statuses = pod_obj.as_dict()["status"]["containerStatuses"]

            for container_status in container_statuses:
                if container_status['name'] == "model-serving":
                    container_state = container_status['state'].keys()
                    if (TERMINATED_STATUS in container_state):
                        error_log = ""
                        pod_logs = pod_obj.logs()
                        for pod_name, pod_log in pod_logs.items():
                            if "model-serving" in pod_name:
                                error_log += pod_log
                        raise MlflowException(
                            f"The pod terminated, see the following logs: \n {error_log}"
                        )

                    elif RUNNING_STATUS in container_state:
                        status_code = requests.get(
                            f"https://{route_host}",
                            auth=(auth_user, auth_password)
                        ).status_code
                        if status_code == 404:
                            # 404 is returned by the server of you call "/" endpoint
                            check_completed = True

                    elif WAITING_STATUS in container_state:
                        watiting_status = container_status['state'][WAITING_STATUS]
                        if "ImagePullBackOff" in watiting_status["reason"]:
                            raise MlflowException(
                                "Image cannot be found: " +
                                container_status['state'][WAITING_STATUS]["message"]
                            )
                    else:
                        continue
        except (IndexError, KeyError):
            logger.info("\n" + "Waiting for pod to start, check again in 5 seconds")
            time.sleep(1)


def get_route_name(name):
    """Retrieves the route name of the openshift application.

    Args:
        name (str): name of the openshift application

    Raises:
        MlflowException: route not found

    Returns:
        str: URL of the route associated with model endpoint
    """
    try:
        route_obj = oc.selector('routes', labels={"app": name}).object()
        return route_obj.as_dict()['spec']['host']
    except OpenShiftPythonException:
        raise MlflowException(f"could not find route information for {name}")


def get_authentication_info(name):
    """Retrieves the authentication information of the model's openshift
    application.

    Args:
        name (name): name of the openshift application

    Returns:
        tuple: authentication user, authentication password
    """
    pod_obj = get_pod_info_from_app_name(name)
    pod_info = pod_obj.as_dict()
    auth_user = ""
    auth_password = ""
    for container_info in pod_info["spec"]["containers"]:
        if container_info["name"] == "auth-proxy":
            for env_var in container_info["env"]:
                if env_var["name"] == "BASIC_AUTH_USERNAME":
                    auth_user = env_var["value"]
                elif env_var["name"] == "BASIC_AUTH_PASSWORD":
                    auth_password = env_var["value"]
                else:
                    continue
    return auth_user, auth_password


def get_pod_info_from_app_name(name):
    """Retrieves the newest (startTime) Pod under the application with the *name*

    Args:
        name (str): name of the openshift application

    Raises:
        MlflowException: no container was started within the timeout period

    Returns:
        openshift.apiobject.APIOoject: containing pod description
    """
    newest_pod = None
    newest_pod_start_time = datetime.datetime(2000, 1, 1, 1, 1, 1)
    retries_left = RETRIES

    if retries_left > 0:
        pod_objs = oc.selector("pods", labels={"app": name}).objects()

        if not pod_objs:
            # no containers for that application, yet
            retries_left -= 1
            time.sleep(SLEEP_TIME)
        else:
            for pod_obj in pod_objs:
                # look for the newest pod if more then one is present
                start_time = pod_obj.as_dict()["status"]["startTime"]
                start_time_dt = datetime.datetime.strptime(
                    start_time, "%Y-%m-%dT%H:%M:%SZ"
                )
                if start_time_dt > newest_pod_start_time:
                    newest_pod_start_time = start_time_dt
                    newest_pod = pod_obj
            return newest_pod
    else:
        timeout = RETRIES*SLEEP_TIME
        raise MlflowException(
            f"Timeout: No new pod was started for {name} within {timeout} seconds")
