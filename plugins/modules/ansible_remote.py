#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ansible_remote
short_description: Manage ansible remotes of a pulp api server instance
description:
  - "This performs CRUD operations on ansible remotes in a pulp api server instance."
options:
  content_type:
    description:
      - Content type of the remote
    type: str
    choices:
      - collection
      - role
    default: role
  collections:
    description:
      - List of collection names to sync
    type: list
    elements: str
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.remote
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of ansible remotes from pulp api server
  ansible_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp ansible remotes
  debug:
    var: remote_status
- name: Create a ansible role remote
  ansible_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    content_type: role
    name: new_ansible_remote
    url: "https://galaxy.ansible.com/api/v1/roles/?namespace__name=ansible"
    state: present
- name: Create a ansible collection remote
  ansible_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    content_type: collection
    name: new_ansible_collection_remote
    url: "https://galaxy-dev.ansible.com/"
    collections:
      - testing.ansible_testing_content
    state: present
- name: Delete a ansible remote
  ansible_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ansible_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of ansible remotes
    type: list
    returned: when no name is given
  remote:
    description: Ansible remote details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpRemoteAnsibleModule,
    PulpAnsibleCollectionRemote,
    PulpAnsibleRoleRemote,
    SqueezerException,
)


def main():
    with PulpRemoteAnsibleModule(
        argument_spec=dict(
            content_type=dict(choices=["collection", "role"], default="role"),
            collections=dict(type="list", elements="str"),
            policy=dict(choices=["immediate"]),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:

        if module.params["content_type"] == "collection":
            RemoteClass = PulpAnsibleCollectionRemote
        else:
            RemoteClass = PulpAnsibleRoleRemote
            if module.params["collections"] is not None:
                raise SqueezerException(
                    "'collections' can only be used for collection remotes."
                )

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in [
                "url",
                "collections",
                "download_concurrency",
                "policy",
                "tls_validation",
            ]
            if module.params[key] is not None
        }

        # Nullifiable values
        if module.params["remote_username"] is not None:
            desired_attributes["username"] = module.params["remote_username"] or None
        if module.params["remote_password"] is not None:
            desired_attributes["password"] = module.params["remote_password"] or None
        desired_attributes.update(
            {
                key: module.params[key] or None
                for key in [
                    "proxy_url",
                    "proxy_username",
                    "proxy_password",
                    "ca_cert",
                    "client_cert",
                    "client_key",
                ]
                if module.params[key] is not None
            }
        )

        RemoteClass(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
