# Test Set-Up
Most of the implemented are integration tests running against an already existing openshift cluster.

## Executing the tests

1. Create a `config.py` file inside the `tests/` directory, containig the following environment setup
        ```
        IMAGE = # existing docker image  
        DOCKER_REGISTRY = #reachable docker registry from within openshift, e.g. openshift docker registry
        TAG = # existing image tag
        MODEL_URI_1 = # uri to an existing mlflow model
        MODEL_URI_2 = # uri to a a second existing mlflow model
        ```

2. Make sure all requirements are installed
    ```
    pip install -r tests/requirements.txt
    ```

3. Log into openshift and select openshift project. Make sure you have admin rights to this project.
    ```
    oc login <token>
    oc project <my-test project>
    ```

4. Run tests using pytest
    ```
    pytest tests/
    ```
