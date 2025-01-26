#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: deb_sync
short_description: Synchronize a deb remote on a pulp server
description:
  - "This module synchronizes a deb remote into a repository."
  - "In check_mode this module assumes, nothing changed upstream."
options:
  remote:
    description:
      - Name of the remote to synchronize
    type: str
    required: true
  repository:
    description:
      - Name of the repository
    type: str
    required: true
  mirror:
    description:
      - Whether to synchronise in mirror mode.
    type: bool
    required: false
    default: false
extends_documentation_fragment:
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Sync deb remote into repository
  pulp.squeezer.deb_sync:
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
    GLUE_DEB_VERSION_SPEC,
    PulpAnsibleModule,
    SqueezerException,
    assert_version,
)

try:
    from pulp_glue.deb import __version__ as pulp_glue_deb_version
    from pulp_glue.deb.context import PulpAptRemoteContext, PulpAptRepositoryContext

    assert_version(GLUE_DEB_VERSION_SPEC, pulp_glue_deb_version, "pulp-glue-deb")
    PULP_GLUE_DEB_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_DEB_IMPORT_ERR = traceback.format_exc()


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue-deb", PULP_GLUE_DEB_IMPORT_ERR)],
        argument_spec={
            "remote": {"required": True},
            "repository": {"required": True},
            "mirror": {"type": "bool", "default": False},
        },
    ) as module:
        repository_ctx = PulpAptRepositoryContext(
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
            remote_ctx = PulpAptRemoteContext(
                module.pulp_ctx, entity={"name": module.params["remote"]}
            )
            payload["remote"] = remote_ctx

        payload["mirror"] = module.params["mirror"]
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
