# Compute Rolling Upgrade Service (CRUS)

**Note:** CRUS is deprecated in CSM 1.2.0. It will be removed in a future CSM release
and replaced with BOS V2, which will provide similar functionality.

CRUS is the Shasta service that manages Compute Node Rolling Upgrades.
It provides a way to upgrade a set of compute nodes in discrete steps
(i.e. a few nodes at a time) gracefully. It coordinates with workload
managers and the Boot Orchestration Service (BOS) to take nodes
out of service, reboot them, and put them back into service while
minimally impacting the availabilty of nodes to do work under a
workload manager.

For further information on CRUS, see:

- [Compute Rolling Upgrade Instructions](docs/Compute_Rolling_Upgrade_Instructions.md)
- [Developer Notes](docs/Developer_Notes.md)
- [Compute Rolling Upgrades](https://github.com/Cray-HPE/docs-csm/blob/main/operations/index.md#compute-rolling-upgrades)

## Logging

The `gunicorn` log level of the CRUS API server is governed by setting the
`CRUS_LOG_LEVEL` environment variable in the `cray-crus` container.
See the [`gunicorn` documentation](https://docs.gunicorn.org/) for valid values
(e.g. `debug`, `info`, `error`, etc). Default if unset is `info`.

The Python logging level of the CRUS upgrade agent is governed by setting the
`CRUA_LOG_LEVEL` environment variable in the `cray-crua` container.
See Python logging module documentation for supported values (e.g. `DEBUG`, `ERROR`,
`INFO`, etc). Default if unset is `INFO`.

## Building

To build a Docker image from the Compute Rolling Upgrade Service code:

```text
$ docker build -t cray-crus .
```

This will build the code and create a docker image called
`cray-crus` tagged as `latest`.

## Running

CRUS can be run in `testing` mode under Docker on any platform:

```text
$ docker run -e CRUS_CONFIGURATION=testing -e ETCD_MOCK_CLIENT=yes -p <your favorite port>:8080 cray-crus
```

This will run the `cray-crus` service in a fully mocked environment in
which you can do simulated upgrades and watch them run to completion.
You can also run this code standalone on a Mac or Linux system
(Windows may also work but has not been attempted) by creating a
virtual environment for `cray-crus`, installing `cray-crus` in that environment,
and running the following command while that virtual environment is
activated:

```text
$ ETCD_MOCK_CLIENT=yes CRUS_CONFIGURATION=testing python -m crus.wsgi
```

See [Development](#Development) for more details.

## Testing

### Unit testing

CRUS uses `nox` to test the Python code. This will check for lint errors
and coding style violations, then run unit tests and verify test coverage.
`nox` will fail if there are lint issues, coding style violations, test
failures, or test coverage of less than 95%.

While the tests provide a leeway that allows for a 95% coverage to
pass, this project tries to maintain 100% coverage with judicious use
of coverage pragmas. The principle here is that it is easier to
review code for test coverage issues if you can identify the code that
is not covered by looking for pragmas than by walking through the
coverage report. Try to maintain 100% coverage and try to
fully justify use of pragmas before using them. There are
several pragmas defined in [`.coveragerc`](.coveragerc) that can be used
and are described there.

To run the tests, go to the top of the source tree and run:

```text
$ nox
```

The tests are also run as part of the Docker image build procedure and
will cause the Docker image build to fail if it the tests do not pass
and reach 95% coverage.

Note that in addition to the tests, the code will be linted and style
checked; no lint or style errors or warnings are permitted.

This same testing is done during the Docker build procedure used both
locally and when building on GitHub. This ensures both lint-free and working code
at build time.

### CT tests

See the [`cms-tools` repository](https://github.com/Cray-HPE/cms-tools) for details
on running CT tests for this service.

### Deploying to hardware for testing

CRUS is Helm based and deploys using Loftsman. To deploy it, follow
the instructions found in
[The Ahoy! README](https://github.com/Cray-HPE/ahoy/blob/master/README.md)
and the Ahoy! manual that is linked from there. Pay attention to the
"Getting Set Up" chapter (Chapter 2) and then use the instructions in the
"Ahoy! Exporting" chapter to get the chart deployed on a system.

## Development

CRUS is intended to be developed in a Python virtual environment. To
set up the virtual environment for development:

1. Create the virtual environment in the root of the cloned tree:

   ```text
   $ virtualenv crus_env
   ```

1. Enter the virtual environment:

   ```text
   $ . ./crus_env/bin/activate
   ```

1. Install CRUS in your workspace virtual environment, which will pull
   in all dependencies.

   ```text
   $ pip install --index-url=http://artifactory.algol60.net/artifactory/csm-python-modules/simple/ --trusted-host artifactory.algol60.net .
   ```

### Important note to developers

The [`openapi.yaml`](api/openapi.yaml) file is kept up to date manually.

### Dependency: `munge-munge`

CRUS uses the `munge` image built by the
[`container-images` repository](https://github.com/Cray-HPE/container-images).
This image is rebuilt periodically to patch security issues, but if
a new version is required, modify the build files in `container-images`
and manually update the version used by `cray-crus`.

CRUS relies on `munge` secrets put in place by PE so periocially this may need
to be updated based on system changes.

### Build helpers

This repo uses some build helpers from the 
[`cms-meta-tools` repository](https://github.com/Cray-HPE/cms-meta-tools).
See that repository for more details.

### Local builds

To perform a local build, the contents of the `cms-meta-tools` repository must be cloned or copied
to `./cms_meta_tools` in the same directory as the [`Makefile`](Makefile). When building
on GitHub, the `cloneCMSMetaTools()` function clones the `cms-meta-tools` repository into that directory.

For a local build, it is necessary to manually write the `.version`, `.docker_version`, and
`.chart_version` files. When building on GitHub, this is done by the `setVersionFiles()` function.

### Versioning

The version `cray-crus` is generated dynamically at build time by running the `version.py` script from
`cms-meta-tools`. The version is included near the very beginning of the GitHub build output.

In order to make it easier to go from an artifact back to the source code that produced that artifact,
a text file named `gitInfo.txt` is added to Docker images built from this repository. Inside the Docker images,
it can be found in the `/` folder. This file contains the branch from which it was built and the most
recent commits to that branch.

For Helm charts, a few annotation metadata fields are appended which contain similar information.

For RPMs, a changelog entry is added with similar information.

### New release branches

When making a new release branch:

- Be sure to set the `.x` and `.y` files to the desired major and minor version number for `cray-crus` for this release. 
- If an `update_external_versions.conf` file exists in this repo, be sure to update that as well, if needed.

## Copyright and license

This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [`LICENSE`](LICENSE) file for details.

When making any modifications to a file that has a Cray/HPE copyright header, that header
must be updated to include the current year.

When creating any new files in this repo, if they contain source code, they must have
the HPE copyright and license text in their header, unless the file is covered under
someone else's copyright/license (in which case that should be in the header). For this
purpose, source code files include Dockerfiles, Ansible files, RPM `spec` files, and shell
scripts. It does **not** include Jenkinsfiles, OpenAPI/Swagger specs, or `README`s.

When in doubt, provided the file is not covered under someone else's copyright or license, then
it does not hurt to add ours to the header.
