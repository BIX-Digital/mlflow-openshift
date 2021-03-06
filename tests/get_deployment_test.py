import unittest
import random
import string

from mlflow.deployments import get_deploy_client

from .config import IMAGE, DOCKER_REGISTRY, APP_NAME, TAG, MODEL_URI_1, \
    TEST_USER, TEST_PASSWORD


class MLflowDeploymenGet(unittest.TestCase):

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
                "tag": TAG,
                "auth_user": TEST_USER,
                "auth_password": TEST_PASSWORD
            }
        )

    def test_get_deployment(self):
        res = self.openshift_client.get_deployment(self.deployment_name)
        self.assertIsNotNone(res['name'])

    def tearDown(self):
        self.openshift_client.delete_deployment(self.deployment_name)
