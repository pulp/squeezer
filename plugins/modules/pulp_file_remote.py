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
    name: new_fiel_remote
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
    PulpAnsibleModule,
    pulp_file,
)


def main():
    module = PulpAnsibleModule(
        argument_spec=dict(
            name=dict(),
            url=dict(),
            download_concurrency=dict(type=int),
            policy=dict(
                choices=['immediate', 'on-demand', 'streamed'],
            ),
            state=dict(
                choices=['present', 'absent'],
            ),
        ),
        supports_check_mode=True,
    )

    changed = False
    state = module.params.pop('state')
    name = module.params['name']
    url = module.params['url']
    download_concurrency = module.params['download_concurrency']
    policy = module.params['policy']

    if name:
        search_result = module.file_remotes_api.list(name=name)
        if search_result.count == 1:
            remote = search_result.results[0]
        else:
            remote = None
        if state == 'present':
            if remote:
                if url and remote.url != url:
                    remote.url = url
                    changed = True
                if download_concurrency and remote.download_concurrency != download_concurrency:
                    remote.download_concurrency = download_concurrency
                    changed = True
                if policy and remote.policy != policy:
                    remote.policy = policy
                    changed = True
                if changed and not module.check_mode:
                    update_response = module.file_remotes_api.update(remote.href, remote)
                    module.wait_for_task(update_response.task)
            else:
                remote = pulp_file.FileRemote(**{k: v for k, v in module.params.items() if v is not None})
                if not module.check_mode:
                    remote = module.file_remotes_api.create(remote)
                changed = True
        if state == 'absent' and remote is not None:
            if not module.check_mode:
                delete_response = module.file_remotes_api.delete(remote.href)
                module.wait_for_task(delete_response.task)
            remote = None
            changed = True
        if remote:
            module.exit_json(changed=changed, file_remote=remote.to_dict())
        else:
            module.exit_json(changed=changed, file_remote=None)
    else:
        remotes = []
        offset = 0
        search_result = module.file_remotes_api.list(limit=module.PAGE_LIMIT, offset=offset)
        remotes.extend(search_result.results)
        while search_result.next:
            offset += module.PAGE_LIMIT
            search_result = module.file_remotes_api.list(limit=module.PAGE_LIMIT, offset=offset)
            remotes.extend(search_result.results)

        module.exit_json(changed=changed, file_remotes=[remote.to_dict() for remote in remotes])


if __name__ == '__main__':
    main()
