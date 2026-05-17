#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


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
  autopublish:
    description:
      - Whether to automatically create publications for new repository versions
    type: bool
  pulp_labels:
    description:
      - A dictionary assigning pulp labels using string keys and values
    type: dict
    version_added: "0.4.0"
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
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

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpFileRepositoryContext = None

DESIRED_KEYS = {
    "autopublish",
    "description",
    "pulp_labels",
}


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpFileRepositoryContext,
        entity_singular="repository",
        entity_plural="repositories",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "name": {},
            "description": {},
            "autopublish": {"type": "bool"},
            "pulp_labels": {"type": "dict"},
        },
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in DESIRED_KEYS if module.params[key] is not None
        }

        # Ensure `pulp_labels` contains only strings for keys and values
        if "pulp_labels" in desired_attributes:
            labels = desired_attributes["pulp_labels"]
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in labels.items()):
                module.fail_json(
                    msg="pulp_labels must be a dictionary with strings as keys and values"
                )

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
