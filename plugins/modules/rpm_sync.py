#!/usr/bin/python

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: rpm_sync
short_description: Synchronize a rpm remote on a pulp server
description:
  - "This module synchronizes a rpm remote into a repository."
  - "In check_mode this module assumes, nothing changed upstream."
options:
  repository:
    description:
      - Name of the repository
    type: str
    required: true
  remote:
    description:
      - Name of the remote to synchronize
    type: str
    required: false
  sync_policy:
    description:
      - Policy to use when syncing.
      - The module will fall back to use the mirror parameter when pulp_rpm version is less than 3.16.
      - The mirror parameter does not support "mirror_content_only" value.
    type: str
    required: false
    default: "additive"
    choices: ["additive", "mirror_complete", "mirror_content_only"]
  skip_types:
    description:
      - List of content types to skip during sync.
    type: list
    required: false
    elements: str
    choices: ["srpm", "treeinfo"]
  optimize:
    description:
      - Whether or not to optimize sync.
    type: bool
    required: false
    default: true
  timeout:
    default: 3600

extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Jacob Floyd (@cognifloyd)
"""

EXAMPLES = r"""
- name: Sync rpm remote into repository
  pulp.squeezer.rpm_sync:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: repo_1
    remote: remote_1
  register: sync_result
- name: Report synched repository version
  debug:
    var: sync_result.repository_version
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
    from pulp_glue.common.context import PluginRequirement
    from pulp_glue.rpm.context import PulpRpmRemoteContext, PulpRpmRepositoryContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "repository": {"required": True},
            "remote": {"required": False},
            "sync_policy": {
                "type": "str",
                "default": "additive",
                "choices": ["additive", "mirror_complete", "mirror_content_only"],
            },
            "skip_types": {
                "type": "list",
                "elements": "str",
                "choices": ["srpm", "treeinfo"],
            },
            "optimize": {"type": "bool", "default": True},
            "timeout": {"type": "int", "default": 3600},
        },
    ) as module:
        repository_ctx = PulpRpmRepositoryContext(
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
            remote_ctx = PulpRpmRemoteContext(
                module.pulp_ctx, entity={"name": module.params["remote"]}
            )
            payload["remote"] = remote_ctx

        sync_policy = module.params["sync_policy"]
        if sync_policy is not None:
            # pulp_rpm supports sync_policy from 3.16.
            # Earlier versions support only mirror.
            if module.pulp_ctx.has_plugin(PluginRequirement("rpm", ">=3.16.0")):
                payload["sync_policy"] = sync_policy
            elif sync_policy == "mirror_content_only":
                raise SqueezerException(
                    "Cannot use sync policy 'mirror_content_only' with pulp_rpm<3.16"
                )
            else:
                payload["mirror"] = sync_policy == "mirror_complete"

        payload.update(
            {
                key: module.params[key]
                for key in [
                    "skip_types",
                    "optimize",
                ]
                if module.params[key] is not None
            }
        )

        repository_version = repository["latest_version_href"]
        # In check_mode, assume nothing changed
        if not module.check_mode:
            sync_task = repository_ctx.sync(body=payload)

            if sync_task["created_resources"]:
                module.set_changed()
                repository_version = sync_task["created_resources"][0]

        module.set_result("repository_version", repository_version)


if __name__ == "__main__":
    main()
