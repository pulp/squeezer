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
      - Version Number to be published
      - Not yet implemented
    type: int
    required: false
  manifest:
    description:
      - Name of the pulp manifest file in the publication
    type: str
    required: false
  state:
    description:
      - State the publication should be in
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
    return: when no name is given
  file_publication:
    description: File publication details
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
            repository=dict(),
            version=dict(),
            manifest=dict(),
            state=dict(
                choices=['present', 'absent'],
            ),
        ),
        required_if=(
            ['state', 'present', ['repository']],
            ['state', 'absent', ['repository']],
        ),
        supports_check_mode=True,
    )

    changed = False
    state = module.params['state']
    repository_name = module.params['repository']
    version = module.params['version']
    manifest = module.params['manifest']

    if version:
        module.fail_json(msg="Selecting a repository version is not yet implemented.")

    if repository_name:
        search_result = module.repositories_api.list(name=repository_name)
        if search_result.count == 1:
            repository = search_result.results[0]
        else:
            module.fail_json(msg="Failed to find repository ({repository_name}).".format(repository_name=repository_name))
        # TODO handle version properly
        repository_version_href = repository.latest_version_href
        # TODO proper search
        # search_result = module.file_publications_api.list(repository_version=repository_version_href)
        # if search_result.count == 1:
        #     publication = search_result.results[0]
        # else:
        #     publication = None
        # ---8<----8<---8<---
        publication = None
        search_result = module.file_publications_api.list()
        for item in search_result.results:
            if item.repository_version == repository_version_href:
                publication = item
                break
        # ---8<----8<---8<---
        if state == 'present':
            if publication:
                # publications cannot be updated
                if manifest and manifest != publication.manifest:
                    module.fail_json(msg="Publications cannot be modified.")
            else:
                publication = pulp_file.FilePublication(repository_version=repository_version_href, manifest=manifest)
                if not module.check_mode:
                    create_response = module.file_publications_api.create(publication)
                    publication_href = module.wait_for_task(create_response.task).created_resources[0]
                    publication = module.file_publications_api.read(publication_href)
                changed = True
        if state == 'absent' and publication is not None:
            if not module.check_mode:
                module.file_publications_api.delete(publication.href)
            publication = None
            changed = True
        if publication:
            module.exit_json(changed=changed, file_publication=publication.to_dict())
        else:
            module.exit_json(changed=changed, file_publication=None)
    else:
        entities = module.list_all(module.file_publications_api)
        module.exit_json(changed=changed, file_publications=[entity.to_dict() for entity in entities])


if __name__ == '__main__':
    main()
