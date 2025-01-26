#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: file_sync
short_description: Synchronize a file remote on a pulp server
description:
  - "This module synchronizes a file remote into a repository."
  - "In check_mode this module assumes, nothing changed upstream."
options:
  repository:
    description:
      - Name of the repository to synchronize into
    type: str
    required: true
  remote:
    description:
      - Name of the remote to synchronize with
    type: str
    required: false
extends_documentation_fragment:
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Sync file remote into repository
  pulp.squeezer.file_sync:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: file_repo_1
    remote: file_remote_1
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
    from pulp_glue.file.context import PulpFileRemoteContext, PulpFileRepositoryContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "repository": {"required": True},
            "remote": {"required": False},
        },
    ) as module:
        repository_ctx = PulpFileRepositoryContext(
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
            remote_ctx = PulpFileRemoteContext(
                module.pulp_ctx, entity={"name": module.params["remote"]}
            )
            payload["remote"] = remote_ctx

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
