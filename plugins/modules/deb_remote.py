#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: deb_remote
short_description: Manage deb remotes of a pulp api server instance
description:
  - "This performs CRUD operations on deb remotes in a pulp api server instance."
options:
  architectures:
    description:
      - List of architectures to sync.
    type: list
    elements: str
  components:
    description:
      - List of components to sync.
    type: list
    elements: str
  distributions:
    description:
      - List of distributions to sync.
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
  sync_installer:
    description:
      - Sync installer packages
    type: bool
    version_added: "0.0.16"
  sync_sources:
    description:
      - Sync source packages
    type: bool
    version_added: "0.0.16"
  sync_udebs:
    description:
      - Sync installer packages
    type: bool
    version_added: "0.0.16"

extends_documentation_fragment:
  - pulp.squeezer.pulp.remote
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of deb remotes from pulp api server
  pulp.squeezer.deb_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp deb remotes
  debug:
    var: remote_status

- name: Create a deb remote
  pulp.squeezer.deb_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_deb_remote
    url: http://localhost/pub/deb/pulp_manifest
    architectures: amd64
    components: 'main contrib non-free'
    distributions: buster
    state: present

- name: Delete a deb remote
  pulp.squeezer.deb_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_deb_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of deb remotes
    type: list
    returned: when no name is given
  remote:
    description: Deb remote details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    GLUE_DEB_VERSION_SPEC,
    PulpRemoteAnsibleModule,
    assert_version,
)

try:
    from pulp_glue.deb import __version__ as pulp_glue_deb_version
    from pulp_glue.deb.context import PulpAptRemoteContext

    assert_version(GLUE_DEB_VERSION_SPEC, pulp_glue_deb_version, "pulp-glue-deb")
    PULP_GLUE_DEB_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_DEB_IMPORT_ERR = traceback.format_exc()
    PulpAptRemoteContext = None


def main():
    with PulpRemoteAnsibleModule(
        context_class=PulpAptRemoteContext,
        import_errors=[("pulp-glue-deb", PULP_GLUE_DEB_IMPORT_ERR)],
        argument_spec={
            "architectures": {"type": "list", "elements": "str"},
            "components": {"type": "list", "elements": "str"},
            "distributions": {"type": "list", "elements": "str"},
            "policy": {"choices": ["immediate", "on_demand", "streamed"]},
            "sync_installer": {"type": "bool"},
            "sync_sources": {"type": "bool"},
            "sync_udebs": {"type": "bool"},
        },
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}

        desired_attributes = {
            key: module.params[key]
            for key in [
                "architectures",
                "components",
                "distributions",
                "sync_installer",
                "sync_sources",
                "sync_udebs",
            ]
            if module.params[key] is not None
        }

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

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
