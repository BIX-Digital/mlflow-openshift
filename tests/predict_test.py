import unittest
import random
import string

from mlflow.deployments import get_deploy_client
import pandas as pd

import numpy as np
from numpy.testing import assert_array_equal

from .config import IMAGE, DOCKER_REGISTRY, TAG, MODEL_URI_1, APP_NAME


class MLflowDeploymenPredict(unittest.TestCase):

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

    def test_predict(self):
        df = pd.DataFrame(
            columns=["sepalLength", "sepalWidth", "petalWidth"],
            data=[[0, 1, 0], [0, 1, 1]]
        )

        res = self.openshift_client.predict(self.deployment_name, df)
        assert_array_equal(res, np.array([0, 0]))

    def tearDown(self):
        self.openshift_client.delete_deployment(self.deployment_name)
