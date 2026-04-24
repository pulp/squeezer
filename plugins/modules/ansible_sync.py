#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: ansible_sync
short_description: Synchronize a ansible remote on a pulp server
description:
  - "This module synchronizes a ansible remote into a repository."
  - "In check_mode this module assumes, nothing changed upstream."
options:
  content_type:
    description:
      - Content type of the remote to be synched
    type: str
    choices:
      - collection
      - role
    default: collection
  remote:
    description:
      - Name of the remote to synchronize
    type: str
    required: false
  repository:
    description:
      - Name of the repository
    type: str
    required: true
  timeout:
    default: 3600
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Sync ansible remote into repository
  pulp.squeezer.ansible_sync:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: ansible_repo_1
    remote: ansible_remote_1
  register: sync_result
- name: Report synched repository version
  debug:
    var: sync_status.repository_version
"""

RETURN = r"""
  repository_version:
    description: Repository version after synching
    type: dict
    returned: always
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    PulpAnsibleModule,
    SqueezerException,
)

try:
    from pulp_glue.ansible.context import (
        PulpAnsibleCollectionRemoteContext,
        PulpAnsibleRepositoryContext,
        PulpAnsibleRoleRemoteContext,
    )

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "content_type": {"choices": ["collection", "role"], "default": "collection"},
            "remote": {"required": False},
            "repository": {"required": True},
            "timeout": {"type": "int", "default": 3600},
        },
    ) as module:
        if module.params["content_type"] == "collection":
            remote_context_class = PulpAnsibleCollectionRemoteContext
        else:
            remote_context_class = PulpAnsibleRoleRemoteContext

        repository_ctx = PulpAnsibleRepositoryContext(
            module.pulp_ctx, entity={"name": module.params["repository"]}
        )
        repository = repository_ctx.entity

        payload = {}
        if module.params["remote"] is None:
            if repository["remote"] is None:
                raise SqueezerException(
                    "No remote was specified and none preconfigured on the repository."
                )
        else:
            remote_ctx = remote_context_class(
                module.pulp_ctx, entity={"name": module.params["remote"]}
            )
            payload["remote"] = remote_ctx
        repository_version = repository["latest_version_href"]
        # In check_mode, assume nothing changed
        if not module.check_mode:
            old_repository_version = repository_version
            sync_result = repository_ctx.sync(body=payload)

            if "content_summary" in sync_result:
                # Looks like a repository version.
                repository_version = sync_result["pulp_href"]
            elif sync_result["created_resources"]:
                # Assume it's a task.
                repository_version = sync_result["created_resources"][0]
            if old_repository_version != repository_version:
                module.set_changed()

        module.set_result("repository_version", repository_version)


if __name__ == "__main__":
    main()
