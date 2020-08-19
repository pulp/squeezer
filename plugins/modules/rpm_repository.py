#!/usr/bin/python
# -*- coding: utf-8 -*-

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
      - Name of the repository to query or manipulate
    type: str
  description:
    description:
      - Description of the repository
    type: str
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Jacob Floyd (@cognifloyd)
"""

EXAMPLES = r"""
- name: Read list of rpm repositories from pulp api server
  rpm_repository:
    api_url: localhost:24817
    username: admin
    password: password
  register: repo_status
- name: Report pulp rpm repositories
  debug:
    var: repo_status
- name: Create a rpm repository
  rpm_repository:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present
- name: Delete a rpm repository
  rpm_repository:
    api_url: localhost:24817
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


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(name=dict(), description=dict()),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:

        natural_key = {"name": module.params["name"]}
        desired_attributes = {}
        if module.params["description"] is not None:
            # In case of an empty string we nullify the description
            desired_attributes["description"] = module.params["description"] or None

        PulpRpmRepository(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
