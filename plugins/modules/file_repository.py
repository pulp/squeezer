#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: file_repository
short_description: Manage file repositories of a pulp api server instance
description:
  - "This performs CRUD operations on file repositories in a pulp api server instance."
options:
  name:
    description:
      - Name of the repository to query or manipulate
    type: str
  description:
    description:
      - Description of the repository
    type: str
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of file repositories from pulp api server
  pulp.squeezer.file_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: repo_status
- name: Report pulp file repositories
  debug:
    var: repo_status

- name: Create a file repository
  pulp.squeezer.file_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present

- name: Delete a file repository
  pulp.squeezer.file_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    state: absent
"""

RETURN = r"""
  repositories:
    description: List of file repositories
    type: list
    returned: when no name is given
  repository:
    description: File repository details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.file.context import PulpFileRepositoryContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpFileRepositoryContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpFileRepositoryContext,
        entity_singular="repository",
        entity_plural="repositories",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            name=dict(),
            description=dict(),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {}
        if module.params["description"] is not None:
            desired_attributes["description"] = module.params["description"]

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
