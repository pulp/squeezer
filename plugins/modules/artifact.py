#!/usr/bin/python

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
  chunk_size:
    description:
      - Size of the chunks to upload a file.
    type: int
    default: 33554432
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of artifacts from pulp server
  pulp.squeezer.artifact:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: artifact_status
- name: Report pulp artifacts
  debug:
    var: artifact_status

- name: Upload a file
  pulp.squeezer.artifact:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    file: local_artifact.txt
    state: present

- name: Delete an artifact by specifying a file
  pulp.squeezer.artifact:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    file: local_artifact.txt
    state: absent

- name: Delete an artifact by specifying the digest
  pulp.squeezer.artifact:
    pulp_url: https://pulp.example.org
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

import os
import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    PulpEntityAnsibleModule,
    SqueezerException,
)

try:
    from pulp_glue.core.context import PulpArtifactContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpArtifactContext = None


class PulpArtifactAnsibleModule(PulpEntityAnsibleModule):
    def process_present(self, entity, natural_key, desired_attributes):
        if entity is None:
            if self.check_mode:
                entity = {**desired_attributes, **natural_key}
            else:
                with open(self.params["file"], "rb") as infile:
                    self.context.upload(
                        infile, sha256=natural_key["sha256"], chunk_size=self.params["chunk_size"]
                    )
                entity = self.context.entity
            self.set_changed()
        return self.represent(entity)


def main():
    with PulpArtifactAnsibleModule(
        context_class=PulpArtifactContext,
        entity_singular="artifact",
        entity_plural="artifacts",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            file=dict(type="path"),
            sha256=dict(),
            chunk_size=dict(type="int", default=33554432),
        ),
        required_if=[("state", "present", ["file"])],
    ) as module:
        sha256 = module.params["sha256"]
        if module.params["file"]:
            if not os.path.exists(module.params["file"]):
                raise SqueezerException("File not found.")
            file_sha256 = module.sha256(module.params["file"])
            if sha256:
                if sha256 != file_sha256:
                    raise SqueezerException("File checksum mismatch.")
            else:
                sha256 = file_sha256

        if sha256 is None and module.state == "absent":
            raise SqueezerException(
                "One of 'file' and 'sha256' is required if 'state' is 'absent'."
            )

        natural_key = {
            "sha256": sha256,
        }

        module.process(natural_key, {})


if __name__ == "__main__":
    main()
