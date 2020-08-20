#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ansible_distribution
short_description: Manage ansible distributions of a pulp server
description:
  - "This performs CRUD operations on ansible distributions in a pulp server."
options:
  name:
    description:
      - Name of the distribution to query or manipulate
    type: str
    required: false
  base_path:
    description:
      - Base path to distribute a publication
    type: str
    required: false
  repository:
    description:
      - Name of the repository to be served
    type: str
    required: false
  version:
    description:
      - Version number of the repository to be served
      - If not specified, the distribution will always serve the latest version.
    type: int
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
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of ansible distributions from pulp api server
  ansible_distribution:
    api_url: localhost:24817
    username: admin
    password: password
  register: distribution_status
- name: Report pulp ansible distributions
  debug:
    var: distribution_status

- name: Create an ansible distribution
  ansible_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_ansible_distribution
    base_path: new/ansible/dist
    repository: my_repository
    state: present

- name: Delete an ansible distribution
  ansible_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_ansible_distribution
    state: absent
"""

RETURN = r"""
  distributions:
    description: List of ansible distributions
    type: list
    returned: when no name is given
  distribution:
    description: Ansible distribution details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpAnsibleDistribution,
    PulpAnsibleRepository,
    PulpContentGuard,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            base_path=dict(),
            repository=dict(),
            version=dict(type="int"),
            content_guard=dict(),
        ),
        required_if=[
            ("state", "present", ["name", "base_path"]),
            ("state", "absent", ["name"]),
        ],
    ) as module:

        repository_name = module.params["repository"]
        version = module.params["version"]
        content_guard_name = module.params["content_guard"]

        natural_key = {
            "name": module.params["name"],
        }
        desired_attributes = {
            key: module.params[key]
            for key in ["base_path"]
            if module.params[key] is not None
        }

        if repository_name:
            repository = PulpAnsibleRepository(module, {"name": repository_name})
            repository.find(failsafe=False)
            # TODO check if version exists
            if version:
                desired_attributes["repository_version"] = repository.entity[
                    "versions_href"
                ] + "{version}/".format(version=version)
            else:
                desired_attributes["repository"] = repository.href

        if content_guard_name is not None:
            if content_guard_name:
                content_guard = PulpContentGuard(module, {"name": content_guard_name})
                content_guard.find(failsafe=False)
                desired_attributes["content_guard"] = content_guard.href
            else:
                desired_attributes["content_guard"] = None

        PulpAnsibleDistribution(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
