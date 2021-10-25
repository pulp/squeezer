![Build Status](https://github.com/pulp/squeezer/workflows/CI/badge.svg)

# Squeezer, an Ansible collection modules for Pulp

This collection provides a set of ansible modules to control a [pulp](https://pulpproject.org) server (version 3) in a descriptive way.
This is neither to be confused with [pulp\_installer](https://github.com/pulp/pulp_installer) to install pulp,
nor [pulp\_ansible](https://github.com/pulp/pulp_ansible) to manage ansible content in pulp.

A lot of inspiration has been drawn from [foreman-ansible-modules](https://github.com/theforeman/foreman-ansible-modules).

## Installation

### Install from Ansible Galaxy

The collection is available from Ansible Galaxy, so you can install it via

    $ ansible-galaxy collection install pulp.squeezer

### Build locally

Alternatively you can building the collection artifact with

    $ make dist

and install the resulting `tar.gz` file with

    $ ansible-galaxy collection install pulp-squeezer-<version>.tar.gz

## Documentation

You can find the inline documentation of each module with `ansible-doc pulp.squeezer.<module_name>`.

## Testing

Testing is done by running handcrafted playbooks from `tests/playbooks` while playing back prerecorded server answers.
Using python virtual environments is recommended.

There is usually one playbook per module that it is meant to test, but that is not a hard requirement.

The playbooks are usually organized in three consecutive plays:

 * The first play is meant to setup the environment.
   Fixtures like dependent pulp resources can be prepared here.
   It runs against `localhost` to prevent recording any vcr tapes.
 * The second play contains the actual tests.
   This usually involves calling the module in question several times with varying parameters and verifying its output.
   Resources created in the first play can be referred to here.
   It is executed on the virtual host `tests` to allow for requests to the REST API and their corresponding responses to be recorded.
 * The third and last play is dedicated to cleanup.
   Any resources created (and maybe left over) in the previous two plays should be removed again here.
   Again with the target `localhost`, this part is not recorded.

During playback, only the prerecorded play in the middle is executed.
Please make sure, that it can run independently from the others.
Also it should not depend on any of the variables defined in `tests/playbooks/vars/server.yaml` other than the connection credentials.

To run the tests, you can either call `make test`, or `make test_<playbook_name>` to only run a specific one.
To perform codestyle linting and ansible sanity checks, run `make lint sanity`.

To (re-)record tests or run live tests, you need a running pulp instance.
Two common ways to provide that development server are explained below.

!!! Warning
    Do not use a production instance, as the tests might perform destructive actions.

### Recording tests against a Pulplift Vagrant environment

A full vm installation of pulp can easily be achieved by using [pulplift](https://github.com/pulp/pulp_installer/blob/master/docs/pulplift.md).
It is recommended to use one of the sandbox installations.
When the vm is up, you need to configure its connection details in `tests/playbooks/vars/server.yaml`.
Squeezer tests can now be run with:

+```
make livetest
+```

The fixtures for the `file_remote` test can be recorded with:

+```
make record_file_remote
+```

### Running tests against a Pulp in one container

The `tests/run_container.sh` script is provided and allows you to run a command with a [Pulp in one](https://pulpproject.org/pulp-in-one-container/) container active.
It requires Docker or Podman to be installed.
The default credentials in `tests/playbooks/vars/server.yaml` are sufficient.
For example, to run all tests against the live Pulp instance:

```
./tests/run_container.sh make livetest
```

Or to record test fixtures for the `rpm_repository` test:

```
./tests/run_container.sh make record_rpm_repository
```

## Licence

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
