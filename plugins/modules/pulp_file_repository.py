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
module: pulp_file_repository
short_description: Manage file repositories of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on file repositories in a pulp api server instance."
options:
  name:
    description:
      - Name of the repository to query or manipulate
    type: str
  description:
    description:
      - Description of the repository
    type: str
  state:
    description:
      - State the repository should be in
    choices:
      - present
      - absent
extends_documentation_fragment:
  - pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of file repositories from pulp api server
  pulp_file_repository:
    api_url: localhost:24817
    username: admin
    password: password
  register: repo_status
- name: Report pulp file repositories
  debug:
    var: repo_status
- name: Create a file repository
  pulp_file_repository:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present
- name: Delete a file repository
  pulp_file_repository:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_repo
    state: absent
'''

RETURN = r'''
  file_repositories:
    description: List of file repositories
    type: list
    return: when no name is given
  file_repository:
    description: File repository details
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
            description=dict(),
        ),
        required_if=[
            ('state', 'present', ['name']),
            ('state', 'absent', ['name']),
        ],
        entity_name='file_repository',
        entity_plural='file_repositories',
    )

    natural_key = {
        'name': module.params['name'],
    }
    desired_attributes = {}
    if module.params['description'] is not None:
        # In case of an empty string we try to nullify the description
        # Which does not yet work
        desired_attributes['description'] = module.params['description'] or None

    module.process_entity(natural_key, desired_attributes)


if __name__ == '__main__':
    main()
