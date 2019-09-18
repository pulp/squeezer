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
module: pulp_repository
short_description: Manage repositories of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on repositories in a pulp api server instance."
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
- name: Read list of repositories from pulp api server
  pulp_repository:
    api_url: localhost:24817
    username: admin
    password: password
  register: repo_status
- name: Report pulp repositories
  debug:
    var: repo_status
- name: Create a repository
  pulp_repository:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present
- name: Delete a repository
  pulp_repository:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_repo
    state: absent
'''

RETURN = r'''
  repositories:
    description: List of repositories
    type: list
    return: when no name is given
  repository:
    description: Repository details
    type: dict
    return: when name is given
'''


from ansible.module_utils.pulp_helper import (
    PulpAnsibleModule,
    pulpcore,
)


def main():
    module = PulpAnsibleModule(
        argument_spec=dict(
            name=dict(),
            description=dict(),
            state=dict(
                choices=['present', 'absent'],
            ),
        ),
        required_if=[
            ('state', 'present', ['name']),
            ('state', 'absent', ['name']),
        ],
        supports_check_mode=True,
    )

    changed = False
    name = module.params['name']
    description = module.params['description']

    if name:
        search_result = module.repositories_api.list(name=name)
        if search_result.count == 1:
            repository = search_result.results[0]
        else:
            repository = None
        if module.params['state'] == 'present':
            if repository:
                if description is not None:
                    if description == "":
                        description = None
                    if repository.description != description:
                        repository.description = description
                        changed = True
                if changed and not module.check_mode:
                    update_response = module.repositories_api.update(repository.href, repository)
                    module.wait_for_task(update_response.task)
            else:
                if description == "":
                    description = None
                repository = pulpcore.Repository(name=name, description=description)
                if not module.check_mode:
                    repository = module.repositories_api.create(repository)
                changed = True
        if module.params['state'] == 'absent' and repository is not None:
            if not module.check_mode:
                delete_response = module.repositories_api.delete(repository.href)
                module.wait_for_task(delete_response.task)
            repository = None
            changed = True
        if repository:
            module.exit_json(changed=changed, repository=repository.to_dict())
        else:
            module.exit_json(changed=changed, repository=None)
    else:
        repositories = []
        page = 1
        search_result = module.repositories_api.list(page=page)
        repositories.extend(search_result.results)
        while len(repositories) < search_result.count:
            page = page + 1
            search_result = module.repositories_api.list(page=page)
            repositories.extend(search_result.results)

        module.exit_json(changed=changed, repositories=[repository.to_dict() for repository in repositories])


if __name__ == '__main__':
    main()
