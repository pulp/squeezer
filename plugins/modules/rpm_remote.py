#!/usr/bin/python


# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: rpm_remote
short_description: Manage rpm remotes of a pulp api server instance
description:
  - "This performs CRUD operations on rpm remotes in a pulp api server instance."
options:
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on_demand
      - streamed
extends_documentation_fragment:
  - pulp.squeezer.pulp.remote
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Jacob Floyd (@cognifloyd)
"""

EXAMPLES = r"""
- name: Read list of rpm remotes from pulp api server
  pulp.squeezer.rpm_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp rpm remotes
  debug:
    var: remote_status

- name: Create a rpm remote
  pulp.squeezer.rpm_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_rpm_remote
    url: https://example.org/centos/8/BaseOS/x86_64/os/
    state: present

- name: Delete a rpm remote
  pulp.squeezer.rpm_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_rpm_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of rpm remotes
    type: list
    returned: when no name is given
  remote:
    description: Rpm remote details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpRemoteAnsibleModule

try:
    from pulp_glue.rpm.context import PulpRpmRemoteContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpRpmRemoteContext = None


def main():
    with PulpRemoteAnsibleModule(
        context_class=PulpRpmRemoteContext,
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "policy": {"choices": ["immediate", "on_demand", "streamed"]},
        },
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}

        module.process(natural_key, {})


if __name__ == "__main__":
    main()
