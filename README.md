[![Build Status](https://travis-ci.com/mdellweg/ansible_modules_pulp.svg?branch=master)](https://travis-ci.com/mdellweg/ansible_modules_pulp)

ansible modules for Pulp aka Squeezer
===

This collection provides a set of ansible modules to control a [pulp](https://pulpproject.org) server (version 3) in a descriptive way.
This is neither to be confused with [ansible-pulp](https://github.com/pulp/ansible-pulp) to install pulp,
nor [pulp\_ansible](https://github.com/pulp/pulp_ansible) to manage ansible content in pulp.

A lot of inspiration has been drawn from [foreman-ansible-modules](https://github.com/theforeman/foreman-ansible-modules).

Available modules
---

* `pulp_ansible_remote`
* `pulp_ansible_repository`
* `pulp_ansible_sync`
* `pulp_artifact`
* `pulp_delete_orphans`
* `pulp_file_content`
* `pulp_file_distribution`
* `pulp_file_publication`
* `pulp_file_remote`
* `pulp_file_repository`
* `pulp_file_sync`
* `pulp_status`

Installation
---

After building the collection artifact with `make dist`, you can install the resulting `tar.gz` file with `ansible-galaxy` in the usual ways.

Documentation
---

You can find the inline documentation of each module with `ansible_doc mdellweg.squeezer.pulp_<...>`.

Testing
---

Testing is done by running handcrafted playbooks from `tests/playbooks` while playing back prerecorded server answers.
Using python virtual environments is recommended.

Those playbooks are meant to test one specific module, and are usually structured in three sections:

 * In the first part, ran against `localhost`, fixtures can be set up.
 * The second part should contain the actual tests and is executed on the virtual host `tests` to allow recording.
 This usually involves calling the module in question several times with varying parameters and verifying it's output.
 * The third part, again for `localhost`, provides the the opportunity to undo part one.

In the first and third parts, no recording takes place.
During playback, only the part in the middle is executed.

To run the tests, you can either call `make test`, or `make test_<playbook_name>` to only run a specific one.
To perform codestyle linting and ansible sanity checks, run `make lint sanity`.

To (re-)record tests, you first need to setup a pulp instance ([pulplift](https://github.com/pulp/pulplift) is recommended here).
With it's connection details configured in `tests/playbooks/vars/server.yaml`, you can run `make record_<playbook_name>`.

Licence
---

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
