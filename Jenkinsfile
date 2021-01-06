// See https://www.opendevstack.org/ods-documentation/ for usage and customization.

@Library('ods-jenkins-shared-library@3.x') _

odsComponentPipeline(
  imageStreamTag: 'ods/jenkins-agent-python:3.0.0',
  branchToEnvironmentMapping: [
    '*': 'dev',
  ],
  'debug': 'true'
) { context ->
    // TODO: add stage liniting
    createTestVirtualenv(context)
    stageTest(context)
    odsComponentStageScanWithSonar(context)
  }


def stageTest(def context) {
  stage('Tests') {
      mlflowEnvVars = getMlflowEnvVars(context)
      sh(
        script: """
            virtualenv testvenv
            . ./testvenv/bin/activate
            export AWS_ACCESS_KEY_ID=${mlflowEnvVars.minioKey}
            export AWS_SECRET_ACCESS_KEY=${mlflowEnvVars.minioSecret}
            export MLFLOW_TRACKING_USERNAME=${mlflowEnvVars.mlflowKey}
            export MLFLOW_TRACKING_PASSWORD=${mlflowEnvVars.mlflowSecret}
            export MLFLOW_TRACKING_URI=https://${mlflowEnvVars.mlflowHost}
            export MLFLOW_S3_ENDPOINT_URL=https://${mlflowEnvVars.minioHost}
            oc project ${context.projectId}-dev
            export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/source/anchors/docker-registry-default.inh-devapps.eu.boehringer.com.pem
            export SSL_CERT_DIR=/etc/pki/ca-trust/source/anchors/
            export SSL_CERT_FILE=/etc/pki/ca-trust/source/anchors/docker-registry-default.inh-devapps.eu.boehringer.com.pem
            python -m pytest -n 4 tests/ --junitxml=tests.xml -o junit_family=xunit2 --cov-report term-missing --cov-report xml --cov=mlflow_openshift -o testpaths=tests
            mkdir -p build/test-results/coverage/
            mv coverage.xml build/test-results/coverage/
            mkdir -p build/test-results/test/
            mv tests.xml build/test-results/test/
        """
    ) 
  }
}


def createTestVirtualenv(def context) {
  stage('Create virtualenv for tests') {
    sh(
      script: """
        virtualenv testvenv
        . ./testvenv/bin/activate
        pip install --upgrade pip
        pip install -r tests/requirements.txt
        python setup.py install
      """
    )
  }
}


def getMlflowEnvVars(def context) {
  return [
      mlflowHost: sh(returnStdout: true, script:"oc -n ${context.projectId}-cd get route mlflow -o jsonpath='{.spec.host}'").trim(),
      mlflowKey: sh(returnStdout: true, script:"oc get secret mlflow-auth-proxy -n ${context.projectId}-cd -o jsonpath='{.data.username}' | base64 --decode").trim(),
      mlflowSecret: sh(returnStdout: true, script:"oc get secret mlflow-auth-proxy -n ${context.projectId}-cd -o jsonpath='{.data.password}' | base64 --decode").trim(),
      minioHost: sh(returnStdout: true, script:"oc -n ${context.projectId}-cd get route s3-minio -o jsonpath='{.spec.host}'").trim(),
      minioKey: sh(returnStdout: true, script:"oc get secret s3-minio-credentials -n ${context.projectId}-cd -o jsonpath='{.data.s3-minio-access-key}' | base64 --decode").trim(),
      minioSecret: sh(returnStdout: true, script:"oc get secret s3-minio-credentials -n ${context.projectId}-cd -o jsonpath='{.data.s3-minio-secret-key}' | base64 --decode ").trim(),
    ]
}
