#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2021, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: access_policy
short_description: Manage access policies in pulp
description:
  - "This module lets you view and change access policies on a pulp3 server."
options:
  viewset_name:
    description:
      - Name of the viewset the access policy is attatched to
    type: str
  statements:
    description:
      - Statements to controll access to certain actions
    type: list
    elements: dict
    suboptions:
      action:
        description: Names of actions on the viewset
        required: true
        type: list
        elements: str
      principal:
        description: Description of the actor
        required: true
        type: str
      condition:
        description:
          - Condition as a string or a list
          - If a list is provided, all conditions are composed with and
        type: raw
      effect:
        description: Effect of the statement
        required: true
        choices:
          - allow
          - deny
        type: str
  creation_hooks:
    description:
      - Hooks to be called on object creation
    aliases:
      - permissions_assignment
    type: list
    elements: dict
    suboptions:
      function:
        description: Function to call
        required: true
        type: str
      parameters:
        description: Parameters for the function call
        required: true
        type: raw
      permissions:
        description: List of permissions to assign to a principal
        required: false
        type: list
        elements: str
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.readonly_entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Dump all access policies
  pulp.squeezer.access_policy:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: access_policies_status
- name: Report the access policies
  debug:
    var: access_policies_status

- name: View the access policy for tasks
  pulp.squeezer.access_policy:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    viewset_name: "tasks"
  register: access_policy_status
- name: Report the access policy
  debug:
    var: access_policy_status

- name: Modify the access policy for tasks
  pulp.squeezer.access_policy:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    viewset_name: "tasks"
    statements:
      - action: "*"
        principal: "*"
        effect: "allow"
    state: present
"""

RETURN = r"""
  access_policies:
    description: List of access policies
    type: list
    returned: when no viewset_name is given
  remote:
    description: Access policy details
    type: dict
    returned: when viewset_name is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    pulp_parse_version,
    PulpEntityAnsibleModule,
    PulpAccessPolicy,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            viewset_name=dict(),
            statements=dict(
                type="list",
                elements="dict",
                options=dict(
                    action=dict(required=True, type="list", elements="str"),
                    principal=dict(required=True),
                    condition=dict(type="raw"),
                    effect=dict(required=True, choices=["allow", "deny"]),
                ),
            ),
            creation_hooks=dict(
                type="list",
                elements="dict",
                options=dict(
                    function=dict(required=True),
                    parameters=dict(required=True, type="raw"),
                    permissions=dict(type="list", elements="str"),
                ),
                aliases=["permissions_assignment"],
            ),
            state=dict(choices=["present"]),
        ),
        required_if=[("state", "present", ["viewset_name"])],
    ) as module:

        natural_key = {"viewset_name": module.params["viewset_name"]}
        desired_attributes = {
            key: module.params[key]
            for key in ["statements", "creation_hooks"]
            if module.params[key] is not None
        }
        if "statements" in desired_attributes:
            for statement in desired_attributes["statements"]:
                if statement["condition"] is None:
                    del statement["condition"]

        # Workaround for rename "permissions_assignment" -> "creation_hooks"
        core_version = (
            module.pulp_api.api_spec.get("info", {})
            .get("x-pulp-app-versions", {})
            .get("core", ())
        )
        if pulp_parse_version(core_version) < pulp_parse_version("3.17.0"):
            if "creation_hooks" in desired_attributes:
                desired_attributes["permissions_assignment"] = desired_attributes.pop(
                    "creation_hooks"
                )

        PulpAccessPolicy(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
