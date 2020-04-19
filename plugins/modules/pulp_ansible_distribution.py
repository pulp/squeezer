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
module: pulp_ansible_distribution
short_description: Manage ansible distributions of a pulp server
description:
  - "This performs CRUD operations on ansible distributions in a pulp server."
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
  repository:
    description:
      - Name of the repository to be served
    type: str
    required: false
  version:
    description:
      - Version number of the repository to be served
      - If not specified, the distribution will always serve the latest version.
    type: int
    required: false
  content_guard:
    description:
      - Name of the content guard for the served content
      - "Warning: This feature is not yet supported."
    type: str
    required: false
extends_documentation_fragment:
  - mdellweg.squeezer.pulp
  - mdellweg.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of ansible distributions from pulp api server
  pulp_ansible_distribution:
    api_url: localhost:24817
    username: admin
    password: password
  register: distribution_status
- name: Report pulp ansible distributions
  debug:
    var: distribution_status

- name: Create an ansible distribution
  pulp_ansible_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_ansible_distribution
    base_path: new/ansible/dist
    repository: my_repository
    state: present

- name: Delete an ansible distribution
  pulp_ansible_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_ansible_distribution
    state: absent
'''

RETURN = r'''
  distributions:
    description: List of ansible distributions
    type: list
    returned: when no name is given
  distribution:
    description: Ansible distribution details
    type: dict
    returned: when name is given
'''


from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import PulpEntityAnsibleModule
from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_ansible_helper import PulpAnsibleDistribution, PulpAnsibleRepository


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            base_path=dict(),
            repository=dict(),
            version=dict(type='int'),
            content_guard=dict(),
        ),
        required_if=[
            ('state', 'present', ['name', 'base_path']),
            ('state', 'absent', ['name']),
        ],
    ) as module:

        repository_name = module.params['repository']
        version = module.params['version']

        if module.params['content_guard']:
            module.fail_json(msg="Content guard features are not yet supported in this module.")

        natural_key = {
            'name': module.params['name'],
        }
        desired_attributes = {
            key: module.params[key] for key in ['base_path', 'content_guard'] if module.params[key] is not None
        }

        if repository_name:
            repository = PulpAnsibleRepository(module, {'name': repository_name}).find()
            if repository is None:
                module.fail_json(msg="Failed to find repository ({repository_name}).".format(repository_name=repository_name))
            # TODO check if version exists
            if version:
                desired_attributes['repository_version'] = repository.versions_href + "{version}/".format(version=version)
            else:
                desired_attributes['repository'] = repository.pulp_href

        PulpAnsibleDistribution(module, natural_key, desired_attributes).process()


if __name__ == '__main__':
    main()
