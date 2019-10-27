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
module: pulp_file_sync
short_description: Synchronize a file remote on a pulp api server instance
version_added: "2.8"
description:
  - "This module synchronizes a file remote into a repository."
options:
  remote:
    description:
      - Name of the remote to synchronize
    type: str
    required: true
  repository:
    description:
      - Name of the repository
    type: str
    required: true
extends_documentation_fragment:
  - pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Sync file remote into repository
  pulp_file_sync:
    api_url: localhost:24817
    username: admin
    password: password
    repository: file_repo_1
    remote: file_remote_1
  register: sync_result
- name: Report pulp repositories
  debug:
    var: sync_status.repository_version
'''

RETURN = r'''
  repository_version:
    description: Repository version after synching
    type: dict
'''


from ansible.module_utils.pulp_helper import PulpAnsibleModule


def main():
    module = PulpAnsibleModule(
        argument_spec=dict(
            remote=dict(required=True),
            repository=dict(required=True),
        ),
    )

    remote_name = module.params['remote']
    repository_name = module.params['repository']

    remote = module.find_entity(module.file_remotes_api, {'name': remote_name})
    if remote is None:
        module.fail_json(msg="Remote '{}' not found.".format(remote_name))

    repository = module.find_entity(module.repositories_api, {'name': repository_name})
    if repository is None:
        module.fail_json(msg="Repository '{}' not found.".format(repository_name))

    result = module.file_remotes_api.sync(remote.pulp_href, {'repository': repository.pulp_href})
    module._changed = True
    sync_task = module.wait_for_task(result.task)
    repository_version = sync_task.created_resources[0]

    module.exit_json(repository_version=repository_version)


if __name__ == '__main__':
    main()
