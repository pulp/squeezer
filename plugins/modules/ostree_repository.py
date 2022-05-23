#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2022, Andrew Block
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ostree_repository
short_description: Manage ostree repositories of a pulp api server instance
description:
  - "This performs CRUD operations on ostree repositories in a pulp api server instance."
options:
  name:
    description:
      - Name of the repository to query or manipulate
    type: str
  description:
    description:
      - Description of the repository
    type: str
  remote:
    description:
      - Name of the remote
    type: str

extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Andrew Block (@sabre1041)
"""

EXAMPLES = r"""
- name: Read list of ostree repositories from pulp api server
  pulp.squeezer.ostree_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: repo_status
- name: Report pulp ostree repositories
  debug:
    var: repo_status

- name: Create a ostree repository
  pulp.squeezer.ostree_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present

- name: Delete a ostree repository
  pulp.squeezer.ostree_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    state: absent
"""

RETURN = r"""
  repositories:
    description: List of ostree repositories
    type: list
    returned: when no name is given
  repository:
    description: Ostree repository details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpOstreeRepository,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            description=dict(),
            remote=dict(),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:

        natural_key = {"name": module.params["name"]}
        desired_attributes = {}
        if module.params["description"] is not None:
            desired_attributes["description"] = module.params["description"] or None

        if module.params["remote"] is not None:
            desired_attributes["remote"] = module.params["remote"] or None

        PulpOstreeRepository(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
