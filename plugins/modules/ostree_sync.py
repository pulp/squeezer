#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2022, Andrew Block
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ostree_sync
short_description: Synchronize a ostree remote on a pulp server
description:
  - "This module synchronizes a ostree remote into a repository."
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
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Andrew Block (@sabre1041)
"""

EXAMPLES = r"""
- name: Sync ostree remote into repository
  pulp.squeezer.ostree_sync:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: ostree_repo_1
    remote: ostree_remote_1
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


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpAnsibleModule,
    PulpOstreeRemote,
    PulpOstreeRepository,
)


def main():
    with PulpAnsibleModule(
        argument_spec=dict(
            remote=dict(required=True),
            repository=dict(required=True),
        ),
    ) as module:

        remote = PulpOstreeRemote(module, {"name": module.params["remote"]})
        remote.find(failsafe=False)

        repository = PulpOstreeRepository(module, {"name": module.params["repository"]})
        repository.find(failsafe=False)

        repository.process_sync(remote)


if __name__ == "__main__":
    main()
