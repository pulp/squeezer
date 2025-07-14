#!/usr/bin/python

# copyright (c) 2025, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: group
short_description: Manage groups of a pulp api server instance
description:
  - "This performs CRUD operations on groups in a pulp api server instance."
options:
  group:
    description:
      - Group object to manipulate
    type: dict
    suboptions:
      name:
        description:
          - Name of the group to query or manipulate
        type: str
        required: true
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of groups from pulp api server
  pulp.squeezer.group:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: groups
- name: Report groups
  debug:
    var: groups
"""

RETURN = r"""
  users:
    description: List of groups
    type: list
    returned: when no group is given
  user:
    description: group details
    type: dict
    returned: when group.name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.core.context import PulpGroupContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpGroupContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpGroupContext,
        entity_singular="group",
        entity_plural="groups",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "group": {
                "type": "dict",
                "options": {
                    "name": {"required": True},
                },
            }
        },
        required_if=[("state", "present", ["group"]), ("state", "absent", ["group"])],
    ) as module:
        group = module.params["group"]
        natural_key = {"name": group and group["name"]}
        desired_attributes = {}

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
