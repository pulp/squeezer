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
module: pulp_file_publication
short_description: Manage file publications of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on file publications in a pulp api server instance."
options:
  repository:
    description:
      - Name of the repository to be published
    type: str
    required: false
  version:
    description:
      - Version number to be published
    type: int
    required: false
  manifest:
    description:
      - Name of the pulp manifest file in the publication
    type: str
    required: false
extends_documentation_fragment:
  - mdellweg.squeezer.pulp
  - mdellweg.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of file publications from pulp api server
  pulp_file_publication:
    api_url: localhost:24817
    username: admin
    password: password
  register: publication_status
- name: Report pulp file publications
  debug:
    var: remote_status
- name: Create a file publication
  pulp_file_publication:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    state: present
- name: Delete a file remote
  pulp_file_remote:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    state: absent
'''

RETURN = r'''
  file_publications:
    description: List of file publications
    type: list
    returned: when no repository is given
  file_publication:
    description: File publication details
    type: dict
    returned: when repository is given
'''


from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import PulpEntityAnsibleModule
from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_file import (
    PulpFilePublication,
    PulpFileRepository,
)


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            repository=dict(),
            version=dict(type='int'),
            manifest=dict(),
        ),
        required_if=(
            ['state', 'present', ['repository']],
            ['state', 'absent', ['repository']],
        ),
    )

    repository_name = module.params['repository']
    version = module.params['version']
    desired_attributes = {
        key: module.params[key] for key in ['manifest'] if module.params[key] is not None
    }

    if repository_name:
        repository = PulpFileRepository(module, {'name': repository_name}).find()
        if repository is None:
            module.fail_json(msg="Failed to find repository ({repository_name}).".format(repository_name=repository_name))
        # TODO check if version exists
        if version:
            repository_version_href = repository.versions_href + "{version}/".format(version=version)
        else:
            repository_version_href = repository.latest_version_href
        natural_key = {'repository_version': repository_version_href}
    else:
        natural_key = {'repository_version': None}

    PulpFilePublication(module, natural_key, desired_attributes).process()


if __name__ == '__main__':
    main()
