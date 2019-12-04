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
module: pulp_file_distribution
short_description: Manage file distributions of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on file distributions in a pulp api server instance."
options:
  name:
    description:
      - Name of the distribution to query or manipulate
    type: str
    required: false
  base_path:
    description:
      - Base path to distribute a publication
    type: str
    required: false
  publication:
    description:
      - Href of the publication to be served
    type: str
    required: false
  content_guard:
    description:
      - Name of the content guard for the served content
    type: str
    requried: false
  state:
    description:
      - State the distribution should be in
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
- name: Read list of file distributions from pulp api server
  pulp_file_distribution:
    api_url: localhost:24817
    username: admin
    password: password
  register: distribution_status
- name: Report pulp file distributions
  debug:
    var: distribution_status

- name: Create a file distribution
  pulp_file_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_file_distribution
    base_path: new/file/dist
    publication: /pub/api/v3/publications/file/file/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/
    state: present
- name: Delete a file distribution
  pulp_file_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_file_distribution
    state: absent
'''

RETURN = r'''
  file_distributions:
    description: List of file distributions
    type: list
    return: when no name is given
  file_distribution:
    description: File distribution details
    type: dict
    return: when name is given
'''


from ansible.module_utils.pulp_helper import PulpEntityAnsibleModule


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            base_path=dict(),
            publication=dict(),
            content_guard=dict(),
        ),
        required_if=[
            ('state', 'present', ['name', 'base_path']),
            ('state', 'absent', ['name']),
        ],
        entity_name='file_distribution',
        entity_plural='file_distributions',
    )

    if module.params['content_guard']:
        module.fail_json(msg="Content guard features are not yet supportet in this module.")

    natural_key = {
        'name': module.params['name'],
    }
    desired_attributes = {
        key: module.params[key] for key in ['base_path', 'content_guard', 'publication'] if module.params[key] is not None
    }

    module.process_entity(natural_key, desired_attributes)


if __name__ == '__main__':
    main()
