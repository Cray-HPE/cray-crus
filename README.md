# Compute Rolling Upgrade Service (CRUS)

CRUS is the Shasta service that manages Compute Node Rolling Upgrades.
It provides a way to upgrade a set of compute nodes in discrete steps
(i.e. a few nodes at a time) gracefully, coordinating with Workload
Managers and with the Boot Orchestration Service (BOS) to take nodes
out of service, boot them and put them back into service while
minimally impacting the availabilty of nodes to do work under a
workload manager.

Further documentation of how to use CRUS can be found in the 'docs'
sub-directory here.

## Logging

The gunicorn log level of the CRUS API server is governed by setting the
CRUS_LOG_LEVEL environment variable in the cray-crus container.
See [gunicorn documentation](https://docs.gunicorn.org/) for valid values
(e.g. debug, info, error, etc). Default if unset is info.

The Python logging level of the CRUS upgrade agent is governed by setting the
CRUA_LOG_LEVEL environment variable in the cray-crua container.
See Python logging module documentation for supported values (e.g. DEBUG, ERROR,
INFO, etc). Default if unset is INFO.

## Building

To build a docker image from the Compute Rolling Upgrade Service code:

```
$ docker build -t cray-crus .
```

This will build the code and create a docker image called
'cray-crus' tagged as latest.

## Running

CRUS can be run in 'testing' mode under Docker on any platform:

```
$ docker run -e CRUS_CONFIGURATION=testing -e ETCD_MOCK_CLIENT=yes -p <your favorite port>:8080 cray-crus
```

This will run the cray-crus service in a fully mocked environment in
which you can do simulated upgrades and watch them run to completion.
You can also run this code standalone on a Mac or Linux system (I
can't vouch for Windows as I have not tried it there) by creating a
virtual environment for cray-crus (see *Development* below),
installing cray crus in that environment (see *Development* below) and
running the following command while that virtual environment is
activated:

```
$ ETCD_MOCK_CLIENT=yes CRUS_CONFIGURATION=testing python -m crus.wsgi
```

## Testing

### Unit Testing

Compute Rolling Upgrade uses nox to test the python code.  This will
check for lint errors and coding style violations, then run unit tests
and verify test coverage.  The tests will fail if there are lint issues,
coding style violations, test failures, or test coverage of less than
95%.

While the tests provide a leeway that allows for a 95% coverage to
pass, this project tries to maintain 100% coverage with judicious use
of coverage pragmas.  The principle here is that it is easier to
review code for test coverage issues if you can identify the code that
is not covered by looking for pragmas than by walking through the
coverage report.  Please try to maintain 100% coverage and try to
fully justify your use of pragmas before using them.  There are
several pragmas defined in .coveragerc that can be used and are
described there.

To run the tests, go to the top of the source tree and run:

```
$ nox
```

The tests are also run as part of the docker image build procedure and
will cause the docker image build to fail if it the tests do not pass
and reach 95% coverage.

Note that in addition to the tests, the code will be linted and style
checked and that no lint or style errors or warnings are permitted.

This same testing is done during the Docker build procedure used both
locally and by Jenkins.  This ensures both lint-free and working code
at Jenkins build time.

### CT Tests

See cms-tools repo for details on running CT tests for this service.

### Deploying to Hardware for Testing

CRUS is Helm based and deploys using Loftsman.  To deploy it, follow
the instructions found in
[The Ahoy! README](https://stash.us.cray.com/projects/CLOUD/repos/loftsman-ahoy/browse/README.md)
and the Ahoy! manual that is linked from there. Make sure you pay
attention to the "Getting Set Up" chapter (Chapter 2) and then use the
instructions in the "Ahoy! Exporting" chapter to get your chart
deployed on a system.

## Development

CRUS is intended to be developed in a Python virtual environment.  To
set up the virtual environment for development:

1. Create the virtual environment in the root of your cloned tree:
   ```
   $ virtualenv crus_env
   ```
2. Enter the virtual environment:
   ```
   $ . ./crus_env/bin/activate
   ```
3. Install the CRUS in your workspace virtual
   environment, which will pull in all dependencies.
   ```
   $ pip install --index-url=http://dst.us.cray.com/piprepo/simple/ --trusted-host dst.us.cray.com .
   ```

### Important Note To Developers

Currently the openapi.yaml file is kept up to date manually. This is to be
changed in the future.

### Dependency: munge-munge
CRUS uses the munge image provided by the wlm-slurm team. 
We specify which major and minor version of the image we want with the 
[update_external_versions.conf](update_external_versions.conf) file.
At build time the [runBuildPrep.sh](runBuildPrep.sh) script finds the
latest version with that major and minor number.

When creating a new release branch, be sure to update this file to specify the
desired major and minor number of the image for the new release.

## Build Helpers
This repo uses some build helper scripts from the 
[cms-meta-tools](https://github.com/Cray-HPE/cms-meta-tools) repo. See that repo for more details.

## Local Builds
If you wish to perform a local build, you will first need to clone or copy the contents of the
cms-meta-tools repo to `./cms_meta_tools` in the same directory as the `Makefile`.

## Versioning
We use [SemVer](http://semver.org/). The version is generated by the version.py script in the
cms-meta-tools repo, and written to the .version file at build time by 
[Jenkinsfile.github](Jenkinsfile.github). It also generates the Docker version and Chart version
 strings, and writes those to .docker_version and .chart_version respectively.

In order to make it easier to go from a version number back to the source code that produced that version,
a text file named gitInfo.txt is added to Docker images and RPMs build from this repo. For Docker images,
it can be found in the /app folder. For RPMs, it is installed on the system under the 
/opt/cray/.rpm_info/*rpm_name*/*version*/*release* directory. This file contains the branch from which
it was built and the most recent commits to that branch. In addition, a few annotation metadata fields
containing similar information are added to the k8s chart.

### Copyright and License
This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [LICENSE](LICENSE) file for details.

When making any modifications to a file that has a Cray/HPE copyright header, that header
must be updated to include the current year.

When creating any new files in this repo, if they contain source code, they must have
the HPE copyright and license text in their header, unless the file is covered under
someone else's copyright/license (in which case that should be in the header). For this
purpose, source code files include Dockerfiles, Ansible files, RPM spec files, and shell
scripts. It does **not** include Jenkinsfiles, OpenAPI/Swagger specs, or READMEs.

When in doubt, provided the file is not covered under someone else's copyright or license, then
it does not hurt to add ours to the header.
