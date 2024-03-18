#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ostree_distribution
short_description: Manage ostree distributions of a pulp api server instance
description:
  - "This performs CRUD operations on ostree distributions in a pulp api server instance."
options:
  name:
    description:
      - Name of the distribution to query or manipulate
    type: str
    required: true
  base_path:
    description:
      - Base path to the distribution
    type: str
    required: true
  repository:
    description:
      - Name of the repository
    type: str
    required: false
  version:
    description:
      - Repository version number
    type: str
    required: false
  content_guard:
    description:
      - Name of the content guard for the served content
      - "Warning: This feature is not yet supported."
    type: str
    required: false
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Andrew Block (@sabre1041)
"""

EXAMPLES = r"""
- name: Read list of ostree distributions from pulp api server
  pulp.squeezer.ostree_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: distribution_status
- name: Report pulp ostree distributions
  debug:
    var: distribution_status

- name: Create a ostree distribution
  pulp.squeezer.ostree_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ostree_distribution
    base_path: new/ostree/dist
    repository: ostree_repository
    state: present

- name: Delete a ostree distribution
  pulp.squeezer.ostree_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ostree_distribution
    state: absent
"""

RETURN = r"""
  distributions:
    description: List of ostree distributions
    type: list
    returned: when no name is given
  distribution:
    description: Ostree distribution details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpOstreeDistribution,
    PulpContentGuard,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            base_path=dict(required=True),
            repository=dict(),
            version=dict(),
            content_guard=dict(),
        ),
        required_if=[
            ("state", "present", ["name", "base_path"]),
            ("state", "absent", ["name"]),
        ],
    ) as module:

        content_guard_name = module.params["content_guard"]

        natural_key = {
            "name": module.params["name"],
        }
        desired_attributes = {
            key: module.params[key]
            for key in ["base_path", "repository"]
            if module.params[key] is not None
        }

        if content_guard_name is not None:
            if content_guard_name:
                content_guard = PulpContentGuard(module, {"name": content_guard_name})
                content_guard.find(failsafe=False)
                desired_attributes["content_guard"] = content_guard.href
            else:
                desired_attributes["content_guard"] = None

        if module.params["version"] is not None:
            desired_attributes["version"] = module.params["version"] or None

        PulpOstreeDistribution(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
