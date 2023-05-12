#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ansible_remote
short_description: Manage ansible remotes of a pulp api server instance
description:
  - This performs CRUD operations on ansible remotes in a pulp api server instance.
options:
  content_type:
    description:
      - Content type of the remote
    type: str
    choices:
      - collection
      - role
    default: collection
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
  collections:
    description:
      - List of Collection requirements.
    type: list
    elements: str
  auth_url:
    description:
      - The URL to receive a session token from, e.g. used with Automation Hub.
    type: str
  token:
    description:
      - The token key to use for authentication.
      - See U(https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#configuring-the-ansible-galaxy-client) for more details.
    type: str
  sync_dependencies:
    description:
      - Sync dependencies for collections specified via requirements file.
    type: bool
  signed_only:
    description:
      - Sync only collections that have a signature.
    type: bool

extends_documentation_fragment:
  - pulp.squeezer.pulp.remote
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of ansible remotes from pulp api server
  pulp.squeezer.ansible_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp ansible remotes
  debug:
    var: remote_status

- name: Create a ansible role remote
  pulp.squeezer.ansible_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    content_type: role
    name: new_ansible_remote
    url: "https://galaxy.ansible.com/api/v1/roles/?namespace__name=ansible"
    state: present

- name: Create a ansible collection remote
  pulp.squeezer.ansible_remote:
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
  pulp.squeezer.ansible_remote:
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


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    PulpRemoteAnsibleModule,
    SqueezerException,
)

try:
    from pulp_glue.ansible.context import (
        PulpAnsibleCollectionRemoteContext,
        PulpAnsibleRoleRemoteContext,
    )
    from pulp_glue.common.context import PulpRemoteContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpRemoteContext = None


def collections_up(collections):
    # Fake yaml ...
    collection_list = "\n".join(("  - " + collection for collection in sorted(collections)))
    return "collections:\n" + collection_list


def collections_down(requirements_file):
    # Fake parse yaml ...
    return sorted(
        collection.lstrip("- ")
        for collection in requirements_file.split("\n")
        if "collections:" not in collection
    )


class PulpAnsibleRemoteAnsibleModule(PulpRemoteAnsibleModule):
    def represent(self, entity):
        entity = super().represent(entity)
        if "requirements_file" in entity:
            entity["collections"] = collections_down(entity["requirements_file"])
        return entity


def main():
    with PulpAnsibleRemoteAnsibleModule(
        context_class=PulpRemoteContext,
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            content_type=dict(choices=["collection", "role"], default="collection"),
            policy=dict(choices=["immediate"]),
            collections=dict(type="list", elements="str"),
            auth_url=dict(),
            token=dict(no_log=True),
            sync_dependencies=dict(type="bool"),
            signed_only=dict(type="bool"),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        if module.params["content_type"] == "collection":
            module.context = PulpAnsibleCollectionRemoteContext(module.pulp_ctx)
        else:
            module.context = PulpAnsibleRoleRemoteContext(module.pulp_ctx)
            for key in ["collections", "auth_url", "token", "sync_dependencies", "signed_only"]:
                if module.params[key] is not None:
                    raise SqueezerException(f"'{key}' can only be used with collection remotes.")

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in [
                "auth_url",
                "token",
                "sync_dependencies",
                "signed_only",
            ]
            if module.params[key] is not None
        }
        if module.params["collections"] is not None:
            desired_attributes["requirements_file"] = collections_up(module.params["collections"])
        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
