# Openshift Mlflow Deployment Client
Mlflow deployment plugin for openshift. This plugin offers the possibility to deploy mlflow packed models into openshift using the regular `mlflow deployment` command line interface.


## Installation
1. Install the mlflow openshift plugin: `python setup.py install`. Later pip install will be added...
2. Make sure the openshift CLI tool is installed by calling `oc` in the command line. If not, you can find an installation tutorial [here](https://docs.openshift.com/enterprise/3.2/cli_reference/get_started_cli.html).
3. Make sure that the python environment contains `mlflow>=1.9`. You can validate it running `pip show mlflow`.  

## Get Started
1. Get your login token from the openshift web-ui use it to log in. You can find it on the top right > question mark > about > command line tools. 
    ```
    oc login <token>
    ```
2. Navigate to the openshift project you want to the deploy the model. Make sure you have admin priviliges in that project. 
    ```
    oc project <my-project>
    ```
    You can validate if your current user has admin rights for the project by executing this command:
    ```
    oc get rolebindings admin -n <my-project>
    ```
3. Setup the mlflow (and s3/minio) environment variables:
    ```
    AWS_ACCESS_KEY_ID=<>
    AWS_SECRET_ACCESS_KEY=<>
    MLFLOW_TRACKING_USERNAME=<>
    MLFLOW_TRACKING_PASSWORD=<>
    MLFLOW_TRACKING_URI=<>
    MLFLOW_S3_ENDPOINT_URL=<>
    ``` 


## Create a Deployment
Creates all necessary artifacts for a model deployment in openshift. 

Mandatory config items
```
--name
--model-uri
--docker-registry
--image
--tag
```

Optional config items
```
--auth_user -> default: `MLFLOW_TRACKING_USERNAME`
--auth_password -> default: `MLFLOW_TRACKING_PASSWORD`
--cpu_limit -> default:
--cpu_request -> default:
--mem_limit -> default:
--mem_request -> default:
--gunicorn_workers -> default: `1`
```

### Example: MLflow CLI
```
mlflow deployments create -t openshift \
    --name <app-name> \
    --model-uri <model-location>
    --config docker_registry=<docker-registry> \
    --config image=<image-name> \
    --config tag=<image_tag>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.create_deployment(
    APP_NAME,
    MODEL_URI,
        "docker_registry": "DOCKER_REGISTRY",
        "image": IMAGE,
        "tag": TAG
    }
)
```

## Updating an existing Deployment
Updates an existing model deployment in openshift. It can either update
        the `model_uri` and/or the mandatory config items describing the container image,
        i.e `image`, `docker_registry`, `tag`.

### Example: MLflow CLI
```
mlflow deployments update -t openshift \
    --name <app-name> \
    --model-uri <model-location>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.update_deployment(
    APP_NAME,
    model_uri=MODEL_URI
)
```

## Deleting a Deyployment
Deletes the deployment and resources (openshift artifacts like routes).

### Example: MLflow CLI
```
mlflow deployments delete -t openshift --name <app_name>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.delete_deployment(APP_NAME)
```


## Listing all Mlflow Deplyoments
Lists all mlflow deployments in the current openshift project.

### Example: MLflow CLI
```
mlflow deployments list -t openshift
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.list_deployments()
```

## Get Deplyoment Information
Retrieves raw, detailed information for the deployment.

### Example: MLflow CLI
```
mlflow deployments get -t openshift --name <app_name>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.get_deployment(APP_NAME)
```


## Predict with Deployment
Makes predictions using the specified deployment name. This can be used for
making batch predictions using the openshift infrastrucutre, e.g. in automated
daily/weekly pipelines. This option is only available for the python mlflow API. However, the REST endpoint can of course be called by and REST capable service.

### Example: python mlflow API
For a iris flower dataset model
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

df = pd.DataFrame(
    columns=["sepalLength", "sepalWidth", "petalWidth"],
    data=[[0, 1, 0], [0, 1, 1]]
)

predictions = openshift_client.predict(APP_NAME, df)
```