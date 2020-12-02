import json
import requests
import ast
import logging
import os

import numpy as np

from mlflow.deployments import BaseDeploymentClient
from mlflow.exceptions import MlflowException

from mlflow_openshift.utils import set_config_defaults
from mlflow_openshift import oc_helper

import openshift as oc


logger = logging.getLogger(__name__)


def target_help():
    help_string = (
        "\nmlflow-openshift plugin integrates openshift to a mlflow deployment pipeline. "
        "For detailed explanation and to see multiple examples, checkout the Readme at "
        "https://bitbucket.biscrum.com/projects/CDS/repos/mlflow-openshift/browse/README.md \n\n"

        "The plugin expects that the user is logged into an openshift cluster using the "
        "official openshift CLI \n"
        "   oc login <token> \n\n"
        "If not installed already, checkout: "
        "https://cookbook.openshift.org/accessing-an-openshift-cluster"
        "/where-can-i-download-the-openshift-command-line-tool.html \n"
        "Additionally, the right openshift project needs to be selected \n"
        "   oc project <myproject> \n\n"

        "Expected environmental variables are identical to an mlflow setup with S3: \n\n"
        "   AWS_ACCESS_KEY_ID=<>\n"
        "   AWS_SECRET_ACCESS_KEY=<>\n"
        "   MLFLOW_TRACKING_USERNAME=<>\n"
        "   MLFLOW_TRACKUNG_PASSWORD=<>\n"
        "   MLFLOW_TRACKING_URI=<>\n"
        "   MLFLOW_S3_ENDPOINT_URL<>\n\n"

        "mlflow deployments create \n"
        "   Creating a deployment will start a new openshift app containing a model serving "
        "container using the `mlflow models serve` "
        "   behind a nginx baed authentication side-car proxy. \n"
        "   Mandatory config items, besides --model-uri and --name, are: \n"
        "       --config docker_registry \n"
        "       --config image \n"
        "   Specifying the docker registry url and the image name. \n"
        "   Information about additional config items, like cpu or memory limit/requests, "
        "   gunicorn-worksers can be found in the official documentation. \n\n"

        "mlflow deployments update \n"
        "   Updating a deployment will only change the specified arguments that are passed.\n"
        "   At this stage, it is only possible to change the model-uri and/or the container image "
        "(docker_registry, image, tag).\n"
        "   For more advanced updates, please consider deleting the old deployment and creating a "
        "new one with the identical name.\n\n"

        "mlflow list/delete/get/predict \n"
        "   These additional functionalities are implemented according to the plugin definition "
        "and require no further explanation."
    )
    return help_string


def run_local(name, model_uri, flavor=None, config={}):
    return NotImplementedError(
        "Running model locally is not supported for the mlflow-openshift plugin.\n"
        "Consider running the mlflow: `mlflow models predict --help` cli for local "
        "batch predictions."
    )


class OpenshiftAPIPlugin(BaseDeploymentClient):
    """Implementation of MLflow's `BaseDeploymentClient` for openshift."""

    def __init__(self, uri):
        super().__init__(uri)
        self.oc_project = oc_helper.get_project_name()

    def create_deployment(self, name, model_uri, flavor=None, config={}):
        """Creates all necessary artifacts for a model deployment in openshift.

        Notes:
            special treatment for different model flavors are not implemented.

        Args:
            name (str): name of the deployment
            model_uri (str): path where to find the mlflow packed model
            flavor (str, optional): mlflow deployment flavor. Defaults to None
            config (dict, optional): config items for the deployment. Defaults to {}
                Necessary config items: image, docker_registry, tag

        Raises:
            mlflow_exception: if the deployment failed in openshift or not all
                mandatory config items are provided

        Returns:
            dict: {'name': <name>, 'flavor': <flavor>}
        """
        if not all(key in config for key in ("image", "docker_registry", "tag")):
            raise MlflowException(
                "not all mandatory config items (image, docker_registry, tag) "
                "are provided."
            )

        config = set_config_defaults(config)
        template_path = os.path.join(
            os.path.dirname(__file__),
            'templates/deploy_with_auth.yml'
        )
        config["NAME"] = name
        config["MODEL_URI"] = model_uri
        oc_helper.apply_deployment_config(config, template_path)

        try:
            route_host = oc_helper.get_route_name(name)
            oc_helper.check_succesful_deployment(
                name, route_host,
                config["BASIC_AUTH_USERNAME"], config["BASIC_AUTH_PASSWORD"]
            )
        except MlflowException as mlflow_exception:
            self.delete_deployment(name)
            raise mlflow_exception

        logger.info("\n" + "Endpoint available under: " + route_host)
        return {'name': name, 'flavor': flavor}

    def delete_deployment(self, name):
        """Deletes the deployment and resources (openshift artifacts like routes).

        Args:
            name (str): name of the deployment
        """
        oc_helper.delete_all_resources(name, self.oc_project)

    def update_deployment(self, name, model_uri=None, flavor=None, config=None):
        """Updates an existing model deployment in openshift. It can either update
        the `model_uri` and/or the mandatory config items describing the container image,
        i.e `image`, `docker_registry`, `tag`.

        Notes:
            In case more configurations need to be changed, consider deleting and creating
            the deployment from scratch.
            Special treatment for different model flavors are not implemented.

        Args:
            name (str): name of the deployment
            model_uri (str): path where to find the mlflow packed model
            flavor (str, optional): mlflow deployment flavor. Defaults to None
            config (dict, optional): config items for the deployment. Defaults to {}

        Raises:
            MlflowException: if the updated deployment lead to an error in openshift

        Returns:
            dict: {'name': <name>, 'flavor': <flavor>}
        """

        if not model_uri and not config:
            raise MlflowException("Provide at least a new *model_uri* or *config*")

        dc_obj = oc.selector("dc", labels={"app": name}).object()
        if config:
            if all(key in config for key in ("image", "docker_registry", "tag")):
                dc_obj = oc_helper.update_container_image(dc_obj, config)
            else:
                raise MlflowException(
                    "Not all of the necessary *config* items for updating are provided. "
                    "You need to provide: image, docker_registry and tag"
                )

        if model_uri:
            dc_obj = oc_helper.update_model_uri(dc_obj, model_uri)

        # hotfix for bug in openshift-client library -> normal apply()
        dc_obj.modify_and_apply(lambda x: True, retries=0)

        route_host = oc_helper.get_route_name(name)
        auth_user, auth_password = oc_helper.get_authentication_info(name)

        try:
            oc_helper.check_succesful_deployment(name, route_host, auth_user, auth_password)
        except MlflowException as mlflow_exception:
            self.delete_deployment(name)
            raise mlflow_exception

        return {'name': name, 'flavor': flavor}

    def list_deployments(self):
        """Lists all mlflow deployments in the current openshift project.

        Notes:
            mlflow deployments are recognized by the label `mlflow` that
            is attached to all deplyoments generated by this plugin.

        Returns:
            list: containing dictionaries for each deployment,
                e.g. [{'name': 'deployment1'}]
        """
        mlflow_deployments = oc.selector("dc", labels={"template": "mlflow"}).names()
        return mlflow_deployments

    def get_deployment(self, name):
        """Retrieves raw, detailed information for the deployment.

        Args:
            name (str): name of the deployment

        Raises:
            MlflowException: no deployment found with that name

        Returns:
            str: raw openshift description of the deployment
        """
        oc_deployment_info = oc_helper.get_raw_pod_info(name)

        if not oc_deployment_info:
            raise MlflowException("No deployment with name: {} found".format(name))
        return {'name': oc_deployment_info}

    def predict(self, deployment_name, df):
        """Makes predictions using the specified deployment name. This can be used for
        making batch predictions using the openshift infrastrucutre, e.g. in automated
        daily/weekly pipelines.

        Args:
            deployment_name (str): name of the deployment
            df (pd.DataFrame): dataframe with the correct format the model expects

        Returns:
            np.ndarray: array containing the predictions
        """
        auth_user, auth_password = oc_helper.get_authentication_info(deployment_name)
        route_host = oc_helper.get_route_name(deployment_name)

        # send to https model deployment
        payload = df.to_dict(orient='split')
        response = requests.post(
            "https://{0}/invocations".format(route_host),
            headers={'Content-Type': 'application/json'},
            auth=(auth_user, auth_password),
            data=json.dumps(payload)
        )
        list_response = ast.literal_eval(response.content.decode("utf-8"))
        return np.array(list_response)
