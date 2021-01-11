import unittest
import os
import random
import string

from mlflow.deployments import get_deploy_client
from mlflow.exceptions import MlflowException

from .config import MODEL_URI_1, IMAGE, DOCKER_REGISTRY, TAG, APP_NAME, \
    TEST_USER, TEST_PASSWORD


class MLflowDeploymentUnitTest(unittest.TestCase):

    def setUp(self):
        target_uri = 'openshift'
        self.openshift_client = get_deploy_client(target_uri)
        self.deployment_name = APP_NAME + ''.join(random.choices(string.ascii_lowercase, k=6))

        self.saved_env = os.environ["AWS_ACCESS_KEY_ID"]

    def test_missing_config_items(self):
        with self.assertRaises(MlflowException):
            self.openshift_client.create_deployment(
                self.deployment_name,
                MODEL_URI_1,
                config={
                    "docker_registry": DOCKER_REGISTRY,
                    "image": "x" + IMAGE,
                }
            )

    def test_missing_env_variable(self):
        with self.assertRaises(MlflowException):
            del os.environ["AWS_ACCESS_KEY_ID"]
            self.openshift_client.create_deployment(
                self.deployment_name,
                MODEL_URI_1,
                config={
                    "docker_registry": DOCKER_REGISTRY,
                    "image": IMAGE,
                    "tag": TAG,
                    "auth_user": TEST_USER,
                    "auth_passowrd": TEST_PASSWORD
                }
            )

    def tearDown(self):
        os.environ["AWS_ACCESS_KEY_ID"] = self.saved_env


# succesful deployment is already part of all other integration tests
class MLflowDeploymentCreateError(unittest.TestCase):

    def setUp(self):
        target_uri = 'openshift'
        self.openshift_client = get_deploy_client(target_uri)
        self.deployment_name = APP_NAME + ''.join(random.choices(string.ascii_lowercase, k=6))

    def test_create_deployment_pod_error(self):
        with self.assertRaises(MlflowException) as error:
            self.openshift_client.create_deployment(
                self.deployment_name,
                "x" + MODEL_URI_1,
                config={
                    "docker_registry": DOCKER_REGISTRY,
                    "image": IMAGE,
                    "tag": TAG,
                    "auth_user": TEST_USER,
                    "auth_password": TEST_PASSWORD
                }
            )
        self.assertTrue(
            "Could not find a registered artifact repository" in error.exception.message)

    def test_create_deployment_wrong_image(self):
        with self.assertRaises(MlflowException):
            self.openshift_client.create_deployment(
                self.deployment_name,
                MODEL_URI_1,
                config={
                    "docker_registry": DOCKER_REGISTRY,
                    "image": "x" + IMAGE,
                    "tag": TAG,
                    "auth_user": TEST_USER,
                    "auth_password": TEST_PASSWORD
                }
            )
