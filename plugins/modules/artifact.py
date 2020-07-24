#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: artifact
short_description: Manage artifacts of a pulp api server instance
description:
  - "This performs CRD operations on artifacts in a pulp api server instance."
options:
  file:
    description:
      - A local file that should be turned into an artifact.
    type: path
  sha256:
    description:
      - sha256 digest of the artifact to query or delete.
      - When specified together with file, it will be used to verify any transaction.
    type: str
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of artifacts from pulp server
  artifact:
    api_url: localhost:24817
    username: admin
    password: password
  register: artifact_status
- name: Report pulp artifacts
  debug:
    var: artifact_status
- name: Upload a file
  artifact:
    api_url: localhost:24817
    username: admin
    password: password
    file: local_artifact.txt
    state: present
- name: Delete an artifact by specifying a file
  artifact:
    api_url: localhost:24817
    username: admin
    password: password
    file: local_artifact.txt
    state: absent
- name: Delete an artifact by specifying the digest
  artifact:
    api_url: localhost:24817
    username: admin
    password: password
    sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    state: absent
"""

RETURN = r"""
  artifacts:
    description: List of artifacts
    type: list
    returned: when no file or sha256 is given
  artifact:
    description: Artifact details
    type: dict
    returned: when file or sha256 is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpArtifact,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(file=dict(type="path"), sha256=dict()),
        required_if=[("state", "present", ["file"])],
    ) as module:

        sha256 = module.params["sha256"]
        if module.params["file"]:
            file_sha256 = module.sha256(module.params["file"])
            if sha256:
                if sha256 != file_sha256:
                    raise Exception("File checksum mismatch.")
            else:
                sha256 = file_sha256

        if sha256 is None and module.params["state"] == "absent":
            raise Exception(
                "One of 'file' and 'sha256' is required if 'state' is 'absent'."
            )

        natural_key = {
            "sha256": sha256,
        }
        uploads = {
            "file": module.params["file"],
        }

        PulpArtifact(module, natural_key, uploads=uploads).process()


if __name__ == "__main__":
    main()
