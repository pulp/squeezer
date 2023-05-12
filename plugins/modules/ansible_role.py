#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ansible_role
short_description: Manage ansible roles of a pulp server
description:
  - "This performs CRUD operations on ansible roles in a pulp server."
options:
  name:
    description:
      - name of the ansible role to query or manipulate
    type: str
  namespace:
    description:
      - namespace the ansible role belongs to
    type: str
  version:
    description:
      - version of the ansible role
    type: str
  sha256:
    description:
      - SHA256 of the ansible role artifact
    type: str
    aliases:
      - digest
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of file content units from pulp api server
  pulp.squeezer.ansible_role:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: content_status
- name: Report pulp ansible roles
  debug:
    var: content_status

- name: Create an ansible role
  pulp.squeezer.ansible_role:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    namespace: geometry
    name: circle
    version: 3.14.1
    sha256: 0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff
    state: present
"""

RETURN = r"""
  contents:
    description: List of ansible roles
    type: list
    returned: when name or namespace or version is not given
  content:
    description: Ansible role details
    type: dict
    returned: when name, namespace and version is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.ansible.context import PulpAnsibleRoleContext
    from pulp_glue.core.context import PulpArtifactContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpAnsibleRoleContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpAnsibleRoleContext,
        entity_singular="content",
        entity_plural="contents",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            name=dict(),
            namespace=dict(),
            version=dict(),
            sha256=dict(aliases=["digest"]),
        ),
        required_if=[
            ("state", "present", ["name", "namespace", "version", "sha256"]),
            ("state", "absent", ["name", "namespace", "version"]),
        ],
    ) as module:
        natural_key = {
            "name": module.params["name"],
            "namespace": module.params["namespace"],
            "version": module.params["version"],
        }
        desired_attributes = {}
        if module.params["sha256"]:
            artifact_ctx = PulpArtifactContext(
                module.pulp_ctx, entity={"sha256": module.params["sha256"]}
            )
            desired_attributes["artifact"] = artifact_ctx.pulp_href

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
