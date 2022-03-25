#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2021, Mark Goddard
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: container_remote
short_description: Manage container remotes of a pulp api server instance
description:
  - "This performs CRUD operations on container remotes in a pulp api server instance."
options:
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on_demand
      - streamed
  upstream_name:
    description:
      - Name of the upstream repository
    type: str
  exclude_tags:
    description:
      - A list of tags to exclude during sync
    type: list
    elements: str
  include_tags:
    description:
      - A list of tags to include during sync
    type: list
    elements: str
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.remote
author:
  - Mark Goddard (@markgoddard)
"""

EXAMPLES = r"""
- name: Read list of container remotes from pulp api server
  pulp.squeezer.container_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp container remotes
  debug:
    var: remote_status

- name: Create a container remote
  pulp.squeezer.container_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_container_remote
    upstream_name: new_container_remote
    url: https://example.org/centos/8/BaseOS/x86_64/os/
    state: present

- name: Delete a container remote
  pulp.squeezer.container_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_container_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of container remotes
    type: list
    returned: when no name is given
  remote:
    description: Container remote details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpRemoteAnsibleModule,
    PulpContainerRemote,
)


def main():
    with PulpRemoteAnsibleModule(
        argument_spec=dict(
            exclude_tags=dict(type="list", elements="str"),
            include_tags=dict(type="list", elements="str"),
            policy=dict(choices=["immediate", "on_demand", "streamed"]),
            upstream_name=dict(),
        ),
        required_if=[
            ("state", "present", ["name", "upstream_name"]),
            ("state", "absent", ["name"]),
        ],
    ) as module:

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in [
                "url",
                "exclude_tags",
                "include_tags",
                "download_concurrency",
                "policy",
                "tls_validation",
                "upstream_name",
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

        PulpContainerRemote(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
