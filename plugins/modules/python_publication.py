#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: python_publication
short_description: Manage python publications of a pulp api server instance
description:
  - "This performs CRUD operations on python publications in a pulp api server instance."
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
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of python publications
  python_publication:
    api_url: localhost:24817
    username: admin
    password: password
  register: publication_status
- name: Report pulp python publications
  debug:
    var: publication_status
- name: Create a python publication
  python_publication:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_python_repo
    state: present
- name: Delete a python publication
  file_publication:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_python_repo
    state: absent
"""

RETURN = r"""
  publications:
    description: List of python publications
    type: list
    returned: when no repository is given
  publication:
    description: Python publication details
    type: dict
    returned: when repository is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpPythonPublication,
    PulpPythonRepository,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            repository=dict(),
            version=dict(type="int"),
        ),
        required_if=(
            ["state", "present", ["repository"]],
            ["state", "absent", ["repository"]],
        ),
    ) as module:

        repository_name = module.params["repository"]
        version = module.params["version"]
        desired_attributes = {}

        if repository_name:
            repository = PulpPythonRepository(module, {"name": repository_name})
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

        PulpPythonPublication(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
