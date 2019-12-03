[![Build Status](https://travis-ci.com/mdellweg/ansible_modules_pulp.svg?branch=master)](https://travis-ci.com/mdellweg/ansible_modules_pulp)

ansible modules for Pulp aka Squeezer
===

This project project aims to provide a complete set of ansible modules to control a pulp3 server in a descriptive way.
This is neither to be confused with ansible-pulp to install pulp, nor pulp\_ansible to manage ansible content in pulp.
It has been wildly inspired by the sister project [foreman-ansible-modules](https://github.com/theforeman/foreman-ansible-modules).

Testing
---

Testing is done by running handcrafted playbooks from `tests/playbooks` while playing back prerecorded server answers.

Those playbooks are meant to test one specific module, and are usually structured in three sections:

 * In the first part, ran against `localhost`, fixtures can be set up.
 * The second part should contain the actual tests and is executet on the virtual host `tests` to allow recording.
 This usually involves calling the module in question several times with variing parameters and verifying it's output.
 * The third part, again for `localhost`, provides the the opportunity to undo part one.

In the first and third parts, no recording takes place.
During playback, only the part in the middle is executed.

To run the tests, you can either call `make test`, or `make test_<playbook_name>` to only run a specific one.

To (re-)record tests, you first need to setup a pulp instance (pulplift is recommended here).
With it's connection details configured in `tests/playbooks/vars/server.yaml`, you can run `make record_<playbook_name>`.
For this step, using python virtual environments is recommended.

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
