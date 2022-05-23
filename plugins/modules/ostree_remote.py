#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2022, Andrew Block
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ostree_remote
short_description: Manage ostree remotes of a pulp api server instance
description:
  - "This performs CRUD operations on ostree remotes in a pulp api server instance."
options:
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on_demand
      - streamed
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.remote
author:
  - Andrew Block (@sabre1041)
"""

EXAMPLES = r"""
- name: Read list of ostree remotes from pulp api server
  pulp.squeezer.ostree_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp ostree remotes
  debug:
    var: remote_status

- name: Create a ostree remote
  pulp.squeezer.ostree_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ostree_remote
    url: http://localhost/pub//pulp_manifest
    state: present

- name: Delete a ostree remote
  pulp.squeezer.ostree_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ostree_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of ostree remotes
    type: list
    returned: when no name is given
  remote:
    description: Ostree remote details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpRemoteAnsibleModule,
    PulpOstreeRemote,
)


def main():
    with PulpRemoteAnsibleModule(
        argument_spec=dict(
            policy=dict(choices=["immediate", "on_demand", "streamed"]),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in ["url", "download_concurrency", "policy", "tls_validation"]
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

        PulpOstreeRemote(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
