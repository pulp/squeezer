#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: file_content
short_description: Manage file content of a pulp api server instance
description:
  - "This performs CRUD operations on file content in a pulp api server instance."
options:
  sha256:
    description:
      - sha256 digest of the file content to query or manipulate
    type: str
    aliases:
      - digest
  relative_path:
    description:
      - Relative path of the file content unit
    type: str
  file:
    description:
      - A path to a file tobe uploaded as the new content unit.
    type: path
  chunk_size:
    description:
      - Chunk size in bytes used to upload the file.
    type: int
    default: 33554432
  repository:
    description:
      - The repository in which the content should be present or absent.
    type: str
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of file content units from pulp api server
  pulp.squeezer.file_content:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: content_status
- name: Report pulp file content units
  debug:
    var: content_status

- name: Create a file content unit
  pulp.squeezer.file_content:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    sha256: 0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff
    relative_path: "data/important_file.txt"
    state: present
"""

RETURN = r"""
  contents:
    description: List of file content units
    type: list
    returned: when digest or relative_path is not given
  content:
    description: File content unit details
    type: dict
    returned: when digest and relative_path is given
"""


import os
import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    PulpEntityAnsibleModule,
    SqueezerException,
)

try:
    from pulp_glue.file.context import PulpFileContentContext, PulpFileRepositoryContext

    PULP_GLUE_IMPORT_ERR = None

except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpFileContentContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpFileContentContext,
        entity_singular="content",
        entity_plural="contents",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "sha256": {"aliases": ["digest"]},
            "relative_path": {},
            "file": {"type": "path"},
            "chunk_size": {"type": "int", "default": 33554432},
            "repository": {},
        },
        required_if=[
            ("state", "present", ["file", "relative_path", "repository"]),
            ("state", "absent", ["relative_path", "repository"]),
        ],
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
            "relative_path": module.params["relative_path"],
        }
        desired_attributes = {}
        defaults = {
            "file": module.params["file"],
            "chunk_size": module.params["chunk_size"],
        }

        if module.params["repository"]:
            module.context.repository_ctx = PulpFileRepositoryContext(
                module.pulp_ctx, entity={"name": module.params["repository"]}
            )

        module.process(natural_key, desired_attributes, defaults=defaults)


if __name__ == "__main__":
    main()
