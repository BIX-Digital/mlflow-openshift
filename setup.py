import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mlflow_openshift",
    version="0.2.3",
    author="sklingel",
    description="MLFlow Openshift Deployment Plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BIX-Digital/mlflow-openshift",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'mlflow>=1.13.*,<2.*',
        'numpy>=1.19.*',
        'openshift-client>=1.0.*'
    ],
    entry_points={"mlflow.deployments": "openshift=mlflow_openshift"}
)
