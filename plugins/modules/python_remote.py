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
  name:
    description:
      - Name of the remote to query or manipulate
    type: str
  url:
    description:
      - URL to the upstream pulp manifest
    type: str
  download_concurrency:
    description:
      - How many downloads should be attempted in parallel
    type: int
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
  proxy_url:
    description:
      - The proxy URL. Format C(scheme://user:password@host:port) .
    type: str
  tls_validation:
    description:
      - If True, TLS peer validation must be performed on remote synchronization.
    type: bool
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of python remotes from pulp api server
  python_remote:
    api_url: localhost:24817
    username: admin
    password: password
  register: remote_status
- name: Report pulp python remotes
  debug:
    var: remote_status
- name: Create a python remote
  python_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_python_remote
    url: https://pypi.org/
    state: present
- name: Delete a python remote
  python_remote:
    api_url: localhost:24817
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
    PulpEntityAnsibleModule,
    PulpPythonRemote,
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
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            url=dict(),
            download_concurrency=dict(type="int"),
            policy=dict(choices=["immediate", "on_demand", "streamed"]),
            proxy_url=dict(),
            tls_validation=dict(type="bool"),
            includes=dict(type="list", elements="str"),
            excludes=dict(type="list", elements="str"),
            prereleases=dict(type="bool"),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in DESIRED_KEYS
            if module.params[key] is not None
        }
        if module.params["proxy_url"] is not None:
            # In case of an empty string we nullify
            desired_attributes["proxy_url"] = module.params["proxy_url"] or None

        PulpPythonRemote(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
