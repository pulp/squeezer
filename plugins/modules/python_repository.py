#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: python_repository
short_description: Manage python repositories of a pulp api server instance
description:
  - "This performs CRUD operations on python repositories in a pulp api server instance."
options:
  name:
    description:
      - Name of the repository to query or manipulate
    type: str
  description:
    description:
      - Description of the repository
    type: str
  autopublish:
    description:
      - Publish new versions automatically.
    required: false
    type: bool
    default: false
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of python repositories from pulp api server
  pulp.squeezer.python_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: repo_status
- name: Report pulp python repositories
  debug:
    var: repo_status

- name: Create a python repository
  pulp.squeezer.python_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present

- name: Delete a python repository
  pulp.squeezer.python_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    state: absent
"""

RETURN = r"""
  repositories:
    description: List of python repositories
    type: list
    returned: when no name is given
  repository:
    description: Python repository details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.python.context import PulpPythonRepositoryContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpPythonRepositoryContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpPythonRepositoryContext,
        entity_singular="repository",
        entity_plural="repositories",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "name": {},
            "description": {},
            "autopublish": {"type": "bool", "default": False},
        },
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            k: module.params[k]
            for k in ("description", "autopublish")
            if module.params.get(k) is not None
        }

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
