#!/usr/bin/python

# copyright (c) 2021, Mark Goddard
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


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
  - pulp.squeezer.pulp.remote
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
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


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpRemoteAnsibleModule

try:
    from pulp_glue.common.context import PluginRequirement
    from pulp_glue.container.context import PulpContainerRemoteContext

    class PulpContainerRemoteContext(PulpContainerRemoteContext):
        def converge(self, desired_attributes, defaults=None):
            if self.pulp_ctx.has_plugin(PluginRequirement("container", specifier=">=2.28.0")):
                # Translate the old name to the new one and back afterwards.
                # Here specifically we can assume there are no defaults.
                # Eventually we expect glue to only expose the new name to us.
                if desired_attributes is not None:
                    if "include_tags" in desired_attributes:
                        desired_attributes["includes"] = desired_attributes.pop("include_tags")
                    if "exclude_tags" in desired_attributes:
                        desired_attributes["excludes"] = desired_attributes.pop("exclude_tags")

                changed, before, after = super().converge(desired_attributes, defaults=defaults)

                if before is not None:
                    if "includes" in before:
                        before["include_tags"] = before.pop("includes")
                    if "excludes" in before:
                        before["exclude_tags"] = before.pop("excludes")
                if after is not None:
                    if "includes" in after:
                        after["include_tags"] = after.pop("includes")
                    if "excludes" in after:
                        after["exclude_tags"] = after.pop("excludes")

                return changed, before, after
            return super().converge(desired_attributes, defaults=defaults)

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpContainerRemoteContext = None


def main():
    with PulpRemoteAnsibleModule(
        context_class=PulpContainerRemoteContext,
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "exclude_tags": {"type": "list", "elements": "str"},
            "include_tags": {"type": "list", "elements": "str"},
            "policy": {"choices": ["immediate", "on_demand", "streamed"]},
            "upstream_name": {},
        },
        required_if=[
            ("state", "present", ["name", "upstream_name"]),
            ("state", "absent", ["name"]),
        ],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in [
                "exclude_tags",
                "include_tags",
                "upstream_name",
            ]
            if module.params[key] is not None
        }

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
