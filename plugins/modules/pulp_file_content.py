#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
---
module: pulp_file_content
short_description: Manage file content of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on file content in a pulp api server instance."
options:
  digest:
    description:
      - sha256 digest of the file content to query or manipulate
    type: str
  relative_path:
    description:
      - Relative path of the file content unit
    type: str
extends_documentation_fragment:
  - mdellweg.squeezer.pulp
  - mdellweg.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of file content units from pulp api server
  pulp_file_content:
    api_url: localhost:24817
    username: admin
    password: password
  register: content_status
- name: Report pulp file content units
  debug:
    var: content_status
- name: Create a file content unit
  pulp_file_content:
    api_url: localhost:24817
    username: admin
    password: password
    digest: 0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff
    relative_path: "data/important_file.txt"
    state: present
'''

RETURN = r'''
  contents:
    description: List of file content units
    type: list
    returned: when digest or relative_path is not given
  content:
    description: File content unit details
    type: dict
    returned: when digest and relative_path is given
'''


from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import PulpEntityAnsibleModule
from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_file import PulpFileContent


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            digest=dict(),
            relative_path=dict(),
        ),
        required_if=[
            ('state', 'present', ['digest', 'relative_path']),
            ('state', 'absent', ['digest', 'relative_path']),
        ],
    )

    natural_key = {
        'digest': module.params['digest'],
        'relative_path': module.params['relative_path']
    }
    desired_attributes = {}

    PulpFileContent(module, natural_key, desired_attributes).process()


if __name__ == '__main__':
    main()
