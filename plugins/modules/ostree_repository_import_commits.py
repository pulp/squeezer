#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2022, Andrew Block
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ostree_repository_import_commits
short_description: Imports commits to a repository on a pulp server
description:
  - "This module imports commits into a repository."
  - "In check_mode this module assumes, nothing changed upstream."
options:
  repository:
    description:
      - Name of the repository to manipulate
    type: str
    required: true
  repository_name:
    description:
      - Name of the repository containing the imported commits
    type: str
    required: true
  file:
    description:
      - A local file that commits should be imported from
    type: str
    required: true
  ref:
    description:
      - Name of the reference
    type: str
    required: false
  parent_commit:
    description:
      - Name of the parent commit
    type: str
    required: false

extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Andrew Block (@sabre1041)
"""

EXAMPLES = r"""
- name: Import commits repository
  pulp.squeezer.ostree_repository_import_commits:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: ostree_repo_1
    repository_name: repo
    file: local_repo.tar
  register: import_commits_result
- name: Report synched repository version
  debug:
    var: import_commits_result.repository_version
"""

RETURN = r"""
  repository_version:
    description: Repository version after importing the commits
    type: dict
    returned: always
"""

import os
from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpAnsibleModule,
    PulpOstreeRepository,
    PulpArtifact,
    SqueezerException,
)


def main():
    with PulpAnsibleModule(
        argument_spec=dict(
            file=dict(required=True),
            repository=dict(required=True),
            repository_name=dict(required=True),
            ref=dict(required=False),
            parent_commit=dict(required=False),
        ),
    ) as module:

        if not os.path.exists(module.params["file"]):
            raise SqueezerException("File not found.")
        sha256 = module.sha256(module.params["file"])

        repository = PulpOstreeRepository(module, {"name": module.params["repository"]})
        repository.find(failsafe=False)

        natural_key = {
            "sha256": sha256,
        }
        uploads = {
            "file": module.params["file"],
        }

        module.params["state"] = "present"

        artifact = PulpArtifact(module, natural_key, uploads=uploads)
        artifact.process()
        artifact.find()

        parameters = {
            "repository_name": module.params["repository_name"],
            "artifact": artifact.entity["pulp_href"],
        }

        ref = module.params["ref"]

        if ref is not None:
            parameters.update({"ref": ref})

        parent_commit = module.params["parent_commit"]

        if parent_commit is not None:
            parameters.update({"parent_commit": parent_commit})

        repository.import_commits(parameters)


if __name__ == "__main__":
    main()
