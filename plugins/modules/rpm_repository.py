#!/usr/bin/python

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: rpm_repository
short_description: Manage rpm repositories of a pulp api server instance
description:
  - "This performs CRUD operations on rpm repositories in a pulp api server instance."
options:
  name:
    description:
      - A unique name of the repository to query or manipulate
      - Required for Create, Update, and Destroy operations
      - If no value is specified, returns a list of all repositories
    type: str
  description:
    description:
      - An optional description of the repository
    type: str
  autopublish:
    description:
      - Whether to automatically create publications for new repository versions
    type: bool
    version_added: "0.0.13"
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Jacob Floyd (@cognifloyd)
  - Aaron Sweeney (@ajsween)
"""

EXAMPLES = r"""
- name: Read list of rpm repositories from pulp api server
  pulp.squeezer.rpm_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: repo_status
- name: Report pulp rpm repositories
  debug:
    var: repo_status

- name: Create a rpm repository
  pulp.squeezer.rpm_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    autopublish: true
    state: present

- name: Delete a rpm repository
  pulp.squeezer.rpm_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    state: absent
"""

RETURN = r"""
  repositories:
    description: List of rpm repositories
    type: list
    returned: when no name is given
  repository:
    description: Rpm repository details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpRpmRepository,
)

DESIRED_KEYS = {"autopublish"}


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(name=dict(), description=dict(), autopublish=dict(type="bool")),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in DESIRED_KEYS if module.params[key] is not None
        }

        if module.params["description"] is not None:
            # In case of an empty string we nullify the description
            desired_attributes["description"] = module.params["description"] or None

        PulpRpmRepository(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
