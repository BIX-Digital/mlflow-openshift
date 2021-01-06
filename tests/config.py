APP_NAME = "a-mlflow-openshift-unittest"

# BI X
# IMAGE = "grndx-dev/newmlservice"
# DOCKER_REGISTRY = "172.30.21.196:5000"
# TAG = "latest"
# MODEL_URI_1 = "s3://mlflow/artifacts/1/0a5f07f173dc45c5b64205da63815e18/artifacts/model-test"
# MODEL_URI_2 = "s3://mlflow/artifacts/1/a3dffe87542144e7a0a7da1bb7e3a101/artifacts/model-test"

# On-premise setup
IMAGE = "cds-dev/ds-ml-service-v2"
DOCKER_REGISTRY = "docker-registry.default.svc:5000"
TAG = "47875a65"
MODEL_URI_1 = "s3://mlflow/artifacts/1/86e69ae20f274a4887cd238934ce5db5/artifacts/model-test"
MODEL_URI_2 = "s3://mlflow/artifacts/1/209de656909e414c93e7dd55c799192d/artifacts/model-test"
