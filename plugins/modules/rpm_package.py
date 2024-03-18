#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: rpm_package
short_description: Manage rpm package content of a pulp api server instance
description:
  - "This performs Create/Read operations on rpm package content in a pulp api server instance."
  - "The API does not have a delete or update operation on rpm packages (ie there is no state=absent for this module)."
options:
  sha256:
    description:
      - sha256 digest of the rpm package content to query or manipulate
    type: str
    aliases:
      - digest
  relative_path:
    description:
      - Relative path of the rpm package content unit (ignored unless creating the package)
    type: str
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Jacob Floyd (@cognifloyd)
  - Daniel Ziegenberg (@ziegenberg)
"""

EXAMPLES = r"""
- name: Read list of rpm package content units from pulp api server
  rpm_package:
    api_url: localhost:24817
    username: admin
    password: password
  register: content_status
- name: Report pulp rpm package content units
  debug:
    var: content_status
- name: Create a rpm package content unit
  rpm_package:
    api_url: localhost:24817
    username: admin
    password: password
    sha256: 0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff
    relative_path: "data/important_package.rpm"
    state: present
"""

RETURN = r"""
  packages:
    description: List of rpm package content units
    type: list
    returned: when digest or relative_path is not given
  package:
    description: The rpm package content unit details
    type: dict
    returned: when digest and relative_path is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpRpmPackageContent,
)


DESIRED_KEYS = {"relative_path"}


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            sha256=dict(aliases=["digest"]),
            relative_path=dict(),
        ),
        required_if=[
            ("state", "present", ["sha256"]),
        ],
    ) as module:

        natural_key = {
            "sha256": module.params["sha256"],
        }
        desired_attributes = {
            key: module.params[key]
            for key in DESIRED_KEYS
            if module.params[key] is not None
        }

        PulpRpmPackageContent(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
