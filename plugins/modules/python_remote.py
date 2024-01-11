#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: python_remote
short_description: Manage python remotes of a pulp api server instance
description:
  - "This performs CRUD operations on python remotes in a pulp api server instance."
options:
  excludes:
    description:
      - List of packages with optional version specifier to exclude from the sync.
    type: list
    elements: str
  includes:
    description:
      - List of packages with optional version specifier to include in the sync.
    type: list
    elements: str
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on_demand
      - streamed
  prereleases:
    description:
      - Whether to include prereleases in the sync.
    type: bool
extends_documentation_fragment:
  - pulp.squeezer.pulp.remote
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of python remotes from pulp api server
  pulp.squeezer.python_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp python remotes
  debug:
    var: remote_status

- name: Create a python remote
  pulp.squeezer.python_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_python_remote
    url: https://pypi.org/
    state: present

- name: Delete a python remote
  pulp.squeezer.python_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_python_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of python remotes
    type: list
    returned: when no name is given
  remote:
    description: Python remote details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpRemoteAnsibleModule

try:
    from pulp_glue.python.context import PulpPythonRemoteContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpPythonRemoteContext = None

DESIRED_KEYS = {
    "prereleases",
    "includes",
    "excludes",
}


def main():
    with PulpRemoteAnsibleModule(
        context_class=PulpPythonRemoteContext,
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            policy=dict(choices=["immediate", "on_demand", "streamed"]),
            includes=dict(type="list", elements="str"),
            excludes=dict(type="list", elements="str"),
            prereleases=dict(type="bool"),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in DESIRED_KEYS if module.params[key] is not None
        }

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
