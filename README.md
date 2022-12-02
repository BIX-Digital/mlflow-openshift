**_IMPORTANT NOTE:_**  This package is no longer maintained and not adapted for mlflow>2.*. 

# Openshift Mlflow Deployment Plugin
Mlflow deployment plugin for openshift. This plugin offers the possibility to deploy mlflow packed models into openshift using the regular `mlflow deployment` command line interface.


## Installation
1. Install the mlflow openshift plugin: `pip install mlflow-openshift`.
2. Make sure the openshift CLI tool is installed by calling `oc` in the command line. If not, you can find an installation tutorial [here](https://docs.openshift.com/container-platform/3.11/cli_reference/get_started_cli.html) 

## Get Started
1. Get your login token from the openshift web-ui and use it to log in. You can find it on the top right > question mark > about > command line tools. 
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
    MLFLOW_S3_ENDPOINT_URL=<>
    ``` 


## Create a Deployment
Creates all necessary artifacts for a model deployment in openshift, i.e. hosting the model in the specified container image and putting and nginx basic authentication proxy in front of the container to publisch an https endpoint.

The succesful deployment will return the created https host. Requests can be sent against mlflow's default `/invocations` endpoint.

Mandatory config items
```
--name
--model-uri
--docker-registry
--image
--tag
--auth_user
--auth_password
```

Optional config items:
```
--cpu_limit -> default: `1`
--cpu_request -> default: `100m`
--mem_limit -> default: `512Mi`
--mem_request -> default: `256Mi`
--gunicorn_workers -> default: `1`
```

### Example: MLflow CLI
```
mlflow deployments create -t openshift \
    --name <name> \
    --model-uri <model-uri>
    --config docker_registry=<docker-registry> \
    --config image=<image> \
    --config tag=<tag>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.create_deployment(
    <name>,
    <model-uri>,
        "docker_registry": <docker_registry>,
        "image": <image>,
        "tag": <tag>
    }
)
```

## Updating an existing Deployment
Updates an existing model deployment in openshift. It can either update
        the `model_uri` and/or the config items describing the container image (all three of them need to be provided),
        i.e `image`, `docker_registry`, `tag`.

### Example: MLflow CLI
```
mlflow deployments update -t openshift \
    --name <name> \
    --model-uri <model-uri>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.update_deployment(
    <name>,
    model_uri=<model-uri>
)
```

## Deleting a Deyployment
Deletes the deployment and resources (openshift artifacts like routes).

### Example: MLflow CLI
```
mlflow deployments delete -t openshift --name <name>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.delete_deployment(<name>)
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
mlflow deployments get -t openshift --name <name>
```

### Example: python mlflow API
```
from mlflow.deployments import get_deploy_client
target_uri = 'openshift'
openshift_client = get_deploy_client(target_uri)

openshift_client.get_deployment(<name>)
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

predictions = openshift_client.predict(<name>, df)
```