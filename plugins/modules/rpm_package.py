#!/usr/bin/python

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: rpm_package
short_description: Manage rpm packages of a pulp api server instance
description:
  - "This performs Create/Read/Remove operations on rpm packages in the context of a repository."
options:
  sha256:
    description:
      - sha256 digest of the rpm package content to query or manipulate
    type: str
    aliases:
      - digest
  file:
    description:
      - A path to a file to be uploaded as the new package.
      - Alternatively this is used to calculate the checksum of the file to be removed.
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
  - Jacob Floyd (@cognifloyd)
  - Daniel Ziegenberg (@ziegenberg)
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: "Read list of rpm packages from pulp api server"
  rpm_package:
    api_url: "localhost:24817"
    username: "admin"
    password: "password"
  register: "content_status"
- name: "Report pulp rpm packages"
  debug:
    var: "content_status"
- name: "Create a rpm package"
  rpm_package:
    api_url: "localhost:24817"
    username: "admin"
    password: "password"
    sha256: "0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff"
    file: "data/important_package.rpm"
    repository: "target_repository"
    state: "present"
"""

RETURN = r"""
  packages:
    description: "List of rpm packages"
    type: "list"
    returned: "when digest and file are not given"
  package:
    description: "The rpm package details"
    type: "dict"
    returned: "when digest or file are given"
"""

import os
import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    PulpEntityAnsibleModule,
    SqueezerException,
)

try:
    from pulp_glue.rpm.context import PulpRpmPackageContext, PulpRpmRepositoryContext

    PULP_GLUE_IMPORT_ERR = None

except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpRpmPackageContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpRpmPackageContext,
        entity_singular="package",
        entity_plural="packages",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "sha256": {"aliases": ["digest"]},
            "file": {"type": "path"},
            "chunk_size": {"type": "int", "default": 33554432},
            "repository": {},
        },
        required_if=[
            ("state", "present", ["file", "repository"]),
            ("state", "absesent", ["repository"]),
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
        }
        desired_attributes = {}
        defaults = {
            "file": module.params["file"],
            "chunk_size": module.params["chunk_size"],
        }

        if module.params["repository"]:
            module.context.repository_ctx = PulpRpmRepositoryContext(
                module.pulp_ctx, entity={"name": module.params["repository"]}
            )

        module.process(natural_key, desired_attributes, defaults=defaults)


if __name__ == "__main__":
    main()
