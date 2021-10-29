#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: deb_publication
short_description: Manage deb publications of a pulp api server instance
description:
  - "This performs CRUD operations on deb publications in a pulp api server instance."
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
  mode:
    description:
      - Mode to use when publishing.
    type: str
    default: simple
    choices: ["structured", "simple",  "simple_and_structured", "verbatim"]
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of deb publications
  deb_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: publication_status
- name: Report pulp deb publications
  debug:
    var: publication_status
- name: Create a deb publication
  deb_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: my_deb_repo
    state: present
- name: Delete a deb publication
  deb_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: my_deb_repo
    state: absent
"""

RETURN = r"""
  publications:
    description: List of deb publications
    type: list
    returned: when no repository is given
  publication:
    description: Deb publication details
    type: dict
    returned: when repository is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpDebPublication,
    PulpDebRepository,
    PulpDebVerbatimPublication,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            repository=dict(),
            version=dict(type="int"),
            mode=dict(
                default="simple",
                choices=["structured", "simple", "simple_and_structured", "verbatim"],
            ),
        ),
        required_if=(
            ["state", "present", ["repository"]],
            ["state", "absent", ["repository"]],
        ),
    ) as module:

        repository_name = module.params["repository"]
        version = module.params["version"]
        mode = module.params["mode"]

        if mode == "verbatim":
            desired_attributes = {}
        else:
            desired_attributes = {
                "simple": "simple" in mode,
                "structured": "structured" in mode,
            }

        if repository_name:
            repository = PulpDebRepository(module, {"name": repository_name})
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
        if mode == "verbatim":
            PulpDebVerbatimPublication(
                module, natural_key, desired_attributes
            ).process()
        else:
            PulpDebPublication(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
