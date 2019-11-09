# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
---
module: pulp_file_remote
short_description: Manage file remotes of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on file remotes in a pulp api server instance."
options:
  name:
    description:
      - Name of the remote to query or manipulate
    type: str
  url:
    description:
      - URL to the upstream pulp manifest
    type: str
  download_conncurrency:
    description:
      - How many downloads should be attempted in parallel
    type: int
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on-demand
      - streamed
  state:
    description:
      - State the remote should be in
    type: str
    choices:
      - present
      - absent
extends_documentation_fragment:
  - pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of file remotes from pulp api server
  pulp_file_remote:
    api_url: localhost:24817
    username: admin
    password: password
  register: remote_status
- name: Report pulp file remotes
  debug:
    var: remote_status
- name: Create a file remote
  pulp_file_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_file_remote
    url: http://localhost/pub/file/pulp_manifest
    state: present
- name: Delete a file remote
  pulp_file_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_file_remote
    state: absent
'''

RETURN = r'''
  file_remotes:
    description: List of file remotes
    type: list
    return: when no name is given
  file_remote:
    description: File remote details
    type: dict
    return: when name is given
'''


from ansible.module_utils.pulp_helper import (
    PulpEntityAnsibleModule,
)


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            url=dict(),
            download_concurrency=dict(type=int),
            policy=dict(
                choices=['immediate', 'on-demand', 'streamed'],
            ),
        ),
        required_if=[
            ('state', 'present', ['name']),
            ('state', 'absent', ['name']),
        ],
        entity_name='file_remote',
        entity_plural='file_remotes',
    )

    natural_key = {
        'name': module.params['name'],
    }
    desired_attributes = {
        key: module.params[key] for key in ['url', 'download_concurrency', 'policy'] if module.params[key] is not None
    }

    module.process_entity(natural_key, desired_attributes)


if __name__ == '__main__':
    main()
