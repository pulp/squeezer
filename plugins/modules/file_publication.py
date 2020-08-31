#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: file_publication
short_description: Manage file publications of a pulp api server instance
description:
  - "This performs CRUD operations on file publications in a pulp api server instance."
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
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of file publications from pulp api server
  file_publication:
    api_url: localhost:24817
    username: admin
    password: password
  register: publication_status
- name: Report pulp file publications
  debug:
    var: publication_status
- name: Create a file publication
  file_publication:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    state: present
- name: Delete a file publication
  file_publication:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    state: absent
"""

RETURN = r"""
  publications:
    description: List of file publications
    type: list
    returned: when no repository is given
  publication:
    description: File publication details
    type: dict
    returned: when repository is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpFilePublication,
    PulpFileRepository,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            repository=dict(),
            version=dict(type="int"),
            manifest=dict(),
        ),
        required_if=(
            ["state", "present", ["repository"]],
            ["state", "absent", ["repository"]],
        ),
    ) as module:

        repository_name = module.params["repository"]
        version = module.params["version"]
        desired_attributes = {
            key: module.params[key]
            for key in ["manifest"]
            if module.params[key] is not None
        }

        if repository_name:
            repository = PulpFileRepository(module, {"name": repository_name})
            repository.find(failsafe=False)
            # TODO check if version exists
            if version:
                repository_version_href = repository.entity[
                    "versions_href"
                ] + "{version}/".format(version=version)
            else:
                repository_version_href = repository.entity["latest_version_href"]
            natural_key = {"repository_version": repository_version_href}
        else:
            natural_key = {"repository_version": None}

        PulpFilePublication(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
