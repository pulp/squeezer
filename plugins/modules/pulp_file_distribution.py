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
  pulp_file_remote:
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


from ansible.module_utils.pulp_helper import (
    PulpAnsibleModule,
    pulp_file,
)


def main():
    module = PulpAnsibleModule(
        argument_spec=dict(
            name=dict(),
            base_path=dict(),
            publication=dict(),
            content_guard=dict(),
            state=dict(
                choices=['present', 'absent'],
            ),
        ),
        required_if=[
            ('state', 'present', ['name', 'base_path']),
            ('state', 'absent', ['name']),
        ],
        supports_check_mode=True,
    )

    changed = False
    state = module.params['state']
    name = module.params['name']
    base_path = module.params['base_path']
    publication_href = module.params['publication']
    content_guard = module.params['content_guard']

    if content_guard:
        module.fail_json(msg="Content guard features are not yet supportet in this module.")

    if name:
        search_result = module.file_distributions_api.list(name=name)
        if search_result.count == 1:
            distribution = search_result.results[0]
        else:
            distribution = None
        if state == 'present':
            if distribution:
                if base_path and distribution.base_path != base_path:
                    distribution.base_path = base_path
                    changed = True
                if publication_href and distribution.publication != publication_href:
                    distribution.publication = publication_href
                    changed = True
                if changed and not module.check_mode:
                    update_response = module.file_distributions_api.update(distribution.href, distribution)
                    module.wait_for_task(update_response.task)
            else:
                distribution = pulp_file.FileDistribution(name=name, base_path=base_path)
                if publication_href:
                    distribution.publication = publication_href
                if not module.check_mode:
                    create_response = module.file_distributions_api.create(distribution)
                    distribution_href = module.wait_for_task(create_response.task).created_resources[0]
                    distribution = module.file_distributions_api.read(distribution_href)
                changed = True
        if state == 'absent' and distribution is not None:
            if not module.check_mode:
                delete_response = module.file_distributions_api.delete(distribution.href)
                module.wait_for_task(delete_response.task)
                distribution = None
            changed = True
        if distribution:
            module.exit_json(changed=changed, file_distribution=distribution.to_dict())
        else:
            module.exit_json(changed=changed, file_distribution=None)
    else:
        distributions = []
        offset = 0
        search_result = module.file_distributions_api.list(limit=module.PAGE_LIMIT, offset=offset)
        distributions.extend(search_result.results)
        while search_result.next:
            offset += module.PAGE_LIMIT
            search_result = module.file_distributions_api.list(limit=module.PAGE_LIMIT, offset=offset)
            distributions.extend(search_result.results)

        module.exit_json(changed=changed, file_distributions=[distribution.to_dict() for distribution in distributions])


if __name__ == '__main__':
    main()
