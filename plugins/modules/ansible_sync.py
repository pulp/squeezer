#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ansible_sync
short_description: Synchronize a ansible remote on a pulp server
description:
  - "This module synchronizes a ansible remote into a repository."
options:
  content_type:
    description:
      - Content type of the remote to be synched
    type: str
    choices:
      - collection
      - role
    default: role
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
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Sync ansible remote into repository
  ansible_sync:
    api_url: localhost:24817
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


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpAnsibleModule,
    PulpAnsibleCollectionRemote,
    PulpAnsibleRoleRemote,
    PulpAnsibleRepository,
)


def main():
    with PulpAnsibleModule(
        argument_spec=dict(
            content_type=dict(choices=["collection", "role"], default="role"),
            remote=dict(required=True),
            repository=dict(required=True),
        ),
    ) as module:

        if module.params["content_type"] == "collection":
            RemoteClass = PulpAnsibleCollectionRemote
        else:
            RemoteClass = PulpAnsibleRoleRemote

        remote = RemoteClass(module, {"name": module.params["remote"]})
        remote.find(failsafe=False)

        repository = PulpAnsibleRepository(
            module, {"name": module.params["repository"]}
        )
        repository.find(failsafe=False)

        repository_version = repository.entity["latest_version_href"]
        sync_task = repository.sync(remote.href)

        if sync_task["created_resources"]:
            module.set_changed()
            repository_version = sync_task["created_resources"][0]

        module.set_result("repository_version", repository_version)


if __name__ == "__main__":
    main()
