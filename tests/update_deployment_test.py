import unittest
import random
import string

from mlflow.deployments import get_deploy_client
from mlflow.exceptions import MlflowException

from .config import IMAGE, DOCKER_REGISTRY, MODEL_URI_1, TAG, \
    APP_NAME, MODEL_URI_2


class MLflowDeploymenUpdate(unittest.TestCase):

    def setUp(self):
        target_uri = 'openshift'
        self.openshift_client = get_deploy_client(target_uri)
        self.deployment_name = APP_NAME + ''.join(random.choices(string.ascii_lowercase, k=6))

        self.openshift_client.create_deployment(
            self.deployment_name,
            MODEL_URI_1,
            config={
                "docker_registry": DOCKER_REGISTRY,
                "image": IMAGE,
                "tag": TAG
            }
        )

    def test_update_deployment_model(self):
        try:
            _ = self.openshift_client.update_deployment(
                self.deployment_name,
                model_uri=MODEL_URI_2,
            )
            raised = False
        except MlflowException:
            raised = True
        self.assertFalse(raised)

    def test_update_deployment_pod_error(self):
        with self.assertRaises(MlflowException) as error:
            _ = self.openshift_client.update_deployment(
                self.deployment_name,
                model_uri="x" + MODEL_URI_2,
            )
        self.assertTrue(
            "Could not find a registered artifact repository" in error.exception.message)

    def tearDown(self):
        self.openshift_client.delete_deployment(self.deployment_name)
