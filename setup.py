from setuptools import setup, find_packages

with open('crus/version.py') as vers_file:
    exec(vers_file.read())  # Get VERSION and API_VERSION from version.py

setup(
    name='crus',
    version=VERSION,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        "marshmallow",
        "shell",
        "apispec >= 0.39.0, < 1",
        "Flask",
        "Flask-RESTful",
        "flask-restful-swagger-2",
        "flask-swagger-ui",
        "flask-marshmallow",
        "etcd3",
        "httpproblem",
        "PyYAML",
        "urllib3",
        "etcd3_model",
        "kubernetes"
    ]
)
