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
  remote:
    description:
      - An optional remote to use by default when syncing
    type: str
    version_added: "0.0.16"
  repo_config:
    description:
      - A JSON document or data structure describing a config.repo file
    type: raw
    version_added: "0.0.16"
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
    remote: existing_remote
    repo_config:
      gpgcheck: 1
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

import json

from ansible.module_utils.six import string_types
from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpRpmRemote,
    PulpRpmRepository,
)

DESIRED_KEYS = {"autopublish", "remote", "repo_config"}


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            description=dict(),
            autopublish=dict(type="bool"),
            remote=dict(),
            repo_config=dict(type="raw"),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in DESIRED_KEYS if module.params[key] is not None
        }

        if module.params["description"] is not None:
            # In case of an empty string we nullify the description
            desired_attributes["description"] = module.params["description"] or None

        if module.params["remote"] is not None:
            remote = PulpRpmRemote(module, {"name": module.params["remote"]})
            remote.find(failsafe=False)
            desired_attributes["remote"] = remote.href

        repo_config = module.params["repo_config"]
        # Encode the repo_config unless its a string, then assume it is pre-formatted JSON
        if repo_config is not None and not isinstance(repo_config, string_types):
            desired_attributes["repo_config"] = json.dumps(repo_config)

        PulpRpmRepository(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
