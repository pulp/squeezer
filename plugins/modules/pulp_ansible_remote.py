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
module: pulp_ansible_remote
short_description: Manage ansible remotes of a pulp api server instance
description:
  - "This performes CRUD operations on ansible remotes in a pulp api server instance."
options:
  name:
    description:
      - Name of the remote to query or manipulate
    type: str
  url:
    description:
      - URL to the upstream galaxy api
    type: str
  download_concurrency:
    description:
      - How many downloads should be attempted in parallel
    type: int
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
  proxy_url:
    description:
      - The proxy URL. Format C(scheme://user:password@host:port) .
    type: str
  tls_validation:
    description:
      - If True, TLS peer validation must be performed on remote synchronization.
    type: bool
extends_documentation_fragment:
  - mdellweg.squeezer.pulp
  - mdellweg.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of ansible remotes from pulp api server
  pulp_ansible_remote:
    api_url: localhost:24817
    username: admin
    password: password
  register: remote_status
- name: Report pulp ansible remotes
  debug:
    var: remote_status
- name: Create a ansible remote
  pulp_ansible_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_ansible_remote
    url: http://localhost/TODO
    state: present
- name: Delete a ansible remote
  pulp_ansible_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_ansible_remote
    state: absent
'''

RETURN = r'''
  remotes:
    description: List of ansible remotes
    type: list
    returned: when no name is given
  remote:
    description: Ansible remote details
    type: dict
    returned: when name is given
'''


from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import PulpEntityAnsibleModule
from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_ansible_helper import PulpAnsibleRemote


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            url=dict(),
            download_concurrency=dict(type='int'),
            policy=dict(
                choices=['immediate'],
            ),
            proxy_url=dict(type='str'),
            tls_validation=dict(type='bool'),
        ),
        required_if=[
            ('state', 'present', ['name']),
            ('state', 'absent', ['name']),
        ]
    ) as module:

        natural_key = {'name': module.params['name']}
        desired_attributes = {
            key: module.params[key] for key in ['url', 'download_concurrency', 'policy', 'proxy_url', 'tls_validation'] if module.params[key] is not None
        }

        PulpAnsibleRemote(module, natural_key, desired_attributes).process()


if __name__ == '__main__':
    main()
