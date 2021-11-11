#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: rpm_sync
short_description: Synchronize a rpm remote on a pulp server
description:
  - "This module synchronizes a rpm remote into a repository."
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
  sync_policy:
    description:
      - Policy to use when syncing.
      - The module will fall back to use the mirror parameter when pulp_rpm version is less than 3.16.
      - The mirror parameter does not support "mirror_content_only" value.
    type: str
    required: false
    default: "additive"
    choices: ["additive", "mirror_complete", "mirror_content_only"]
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Jacob Floyd (@cognifloyd)
"""

EXAMPLES = r"""
- name: Sync rpm remote into repository
  rpm_sync:
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


import re

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpAnsibleModule,
    PulpRpmRemote,
    PulpRpmRepository,
    SqueezerException,
)


def _parse_version(version_str):
    """Return a version string as a list of ints or strings."""
    # Examples:
    # "1.2.3" -> [1, 2, 3]
    # "1.2.3-dev" -> [1, 2, 3, "dev"]

    def try_convert_int(i):
        try:
            return int(i)
        except ValueError:
            return i

    return [try_convert_int(i) for i in re.split(r"[\.\-]", version_str)]


def main():
    with PulpAnsibleModule(
        argument_spec=dict(
            remote=dict(required=True),
            repository=dict(required=True),
            sync_policy=dict(
                type="str",
                default="additive",
                choices=["additive", "mirror_complete", "mirror_content_only"],
            ),
        ),
    ) as module:

        remote = PulpRpmRemote(module, {"name": module.params["remote"]})
        remote.find(failsafe=False)

        repository = PulpRpmRepository(module, {"name": module.params["repository"]})
        repository.find(failsafe=False)

        # pulp_rpm supports sync_policy from 3.16.
        # Earlier versions support only mirror.
        rpm_version = (
            module.pulp_api.api_spec.get("info", {})
            .get("x-pulp-app-versions", {})
            .get("rpm", ())
        )
        if _parse_version(rpm_version) >= _parse_version("3.16.0"):
            parameters = {"sync_policy": module.params["sync_policy"]}
        elif module.params["sync_policy"] == "mirror_content_only":
            raise SqueezerException(
                "Cannot use sync policy 'mirror_content_only' with pulp_rpm<3.16"
            )
        else:
            mirror = module.params["sync_policy"] == "mirror_complete"
            parameters = {"mirror": mirror}

        repository.process_sync(remote, parameters)


if __name__ == "__main__":
    main()
