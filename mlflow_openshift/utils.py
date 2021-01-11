import os
import logging

from mlflow.exceptions import MlflowException

from mlflow_openshift.defaults import GUNICORN_WORKERS, \
    CPU_REQUEST, CPU_LIMIT, \
    MEM_REQUEST, MEM_LIMIT


logger = logging.getLogger(__name__)


def set_config_defaults(config):
    """Sets all default values for not mandatory config items.

    Args:
        config (dict): containing all config items that can't be covered
             natively by the mlflow CLI API

    Returns:
        dict: patched config argument with default values
    """
    try:
        config["mlflow_s3_endpoint_url"] = os.environ["MLFLOW_S3_ENDPOINT_URL"]
        config["aws_access_key_id"] = os.environ["AWS_ACCESS_KEY_ID"]
        config["aws_secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
    except KeyError:
        required_envs = [
            "MLFLOW_S3_ENDPOINT_URL",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY"
        ]
        for env in required_envs:
            try:
                os.environ[env]
            except KeyError:
                break
        raise MlflowException(f"Required environment variables {env} is not set.")

    # rename for nginx auth proxy
    config["basic_auth_username"] = config["auth_user"]
    config["basic_auth_password"] = config["auth_password"]
    del config["auth_user"]
    del config["auth_password"]

    if "gunicorn_workers" not in config:
        config["gunicorn_workers"] = GUNICORN_WORKERS

    if "mem_request" not in config:
        config["mem_request"] = MEM_REQUEST

    if "cpu_request" not in config:
        config["cpu_request"] = CPU_REQUEST

    if "cpu_limit" not in config:
        config["cpu_limit"] = CPU_LIMIT

    if "mem_limit" not in config:
        config["mem_limit"] = MEM_LIMIT

    config["tagversion"] = config["tag"]

    del config["tag"]

    upper_config = {k.upper(): v for k, v in config.items()}
    return upper_config
