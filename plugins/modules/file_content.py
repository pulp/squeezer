#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


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
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of file content units from pulp api server
  file_content:
    api_url: localhost:24817
    username: admin
    password: password
  register: content_status
- name: Report pulp file content units
  debug:
    var: content_status
- name: Create a file content unit
  file_content:
    api_url: localhost:24817
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


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpFileContent,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            sha256=dict(aliases=["digest"]),
            relative_path=dict(),
        ),
        required_if=[
            ("state", "present", ["sha256", "relative_path"]),
            ("state", "absent", ["sha256", "relative_path"]),
        ],
    ) as module:

        natural_key = {
            "sha256": module.params["sha256"],
            "relative_path": module.params["relative_path"],
        }
        desired_attributes = {}

        PulpFileContent(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
