#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


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
    from pulp_glue.common.context import PulpEntityNotFound
    from pulp_glue.core.context import PulpArtifactContext as _PulpArtifactContext

    PULP_GLUE_IMPORT_ERR = None

    # Patch the Context to make converge call upload
    # It's a case study at this point. Eventually glue should handle this.
    class PulpArtifactContext(_PulpArtifactContext):
        def converge(self, desired_attributes, defaults=None):
            """
            Converge an entity to have a set of desired attributes.

            This will look for the entity, and depending on what it found and what should be, create,
            delete or update the entity.

            Parameters:
                desired_attributes: Dictionary of attributes the entity should have.

            Returns:
                Tuple of (changed, before, after)
            """
            try:
                entity = self.entity
            except PulpEntityNotFound:
                entity = None

            if desired_attributes is None:
                if entity is not None:
                    # raise SqueezerException("Artifacts cannot be deleted")
                    self.delete()
                    return True, entity, None
            else:
                if entity is None:
                    # This is being quite different:
                    with open(defaults["file"], "rb") as file:
                        self.upload(
                            file=file,
                            chunk_size=defaults["chunk_size"],
                            sha256=self._entity_lookup["sha256"],
                        )
                    return True, None, self.entity
            return False, entity, entity

except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpArtifactContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpArtifactContext,
        entity_singular="artifact",
        entity_plural="artifacts",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "file": {"type": "path"},
            "sha256": {},
            "chunk_size": {"type": "int", "default": 33554432},
        },
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
        desired_attributes = {}
        defaults = {
            "file": module.params["file"],
            "chunk_size": module.params["chunk_size"],
        }

        module.process(natural_key, desired_attributes, defaults=defaults)


if __name__ == "__main__":
    main()
