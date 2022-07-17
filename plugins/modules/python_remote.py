#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: python_remote
short_description: Manage python remotes of a pulp api server instance
description:
  - "This performs CRUD operations on python remotes in a pulp api server instance."
options:
  excludes:
    description:
      - List of packages with optional version specifier to exclude from the sync.
    type: list
    elements: str
  includes:
    description:
      - List of packages with optional version specifier to include in the sync.
    type: list
    elements: str
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on_demand
      - streamed
  prereleases:
    description:
      - Whether to include prereleases in the sync.
    type: bool
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.remote
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of python remotes from pulp api server
  pulp.squeezer.python_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp python remotes
  debug:
    var: remote_status

- name: Create a python remote
  pulp.squeezer.python_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_python_remote
    url: https://pypi.org/
    state: present

- name: Delete a python remote
  pulp.squeezer.python_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_python_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of python remotes
    type: list
    returned: when no name is given
  remote:
    description: Python remote details
    type: dict
    returned: when name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpPythonRemote,
    PulpRemoteAnsibleModule,
)

DESIRED_KEYS = {
    "url",
    "download_concurrency",
    "policy",
    "tls_validation",
    "prereleases",
    "includes",
    "excludes",
}


def main():
    with PulpRemoteAnsibleModule(
        argument_spec=dict(
            policy=dict(choices=["immediate", "on_demand", "streamed"]),
            includes=dict(type="list", elements="str"),
            excludes=dict(type="list", elements="str"),
            prereleases=dict(type="bool"),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in DESIRED_KEYS if module.params[key] is not None
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

        PulpPythonRemote(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
