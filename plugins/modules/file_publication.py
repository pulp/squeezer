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
  pulp.squeezer.file_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: publication_status
- name: Report pulp file publications
  debug:
    var: publication_status

- name: Create a file publication
  pulp.squeezer.file_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: my_file_repo
    state: present

- name: Delete a file publication
  pulp.squeezer.file_publication:
    pulp_url: https://pulp.example.org
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


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.file.context import PulpFilePublicationContext, PulpFileRepositoryContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpFilePublicationContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpFilePublicationContext,
        entity_singular="publication",
        entity_plural="publications",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
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
            key: module.params[key] for key in ["manifest"] if module.params[key] is not None
        }

        if repository_name:
            repository_ctx = PulpFileRepositoryContext(
                module.pulp_ctx, entity={"name": repository_name}
            )
            repository = repository_ctx.entity
            # TODO check if version exists
            if version:
                repository_version_href = repository["versions_href"] + f"{version}/"
            else:
                repository_version_href = repository["latest_version_href"]
            natural_key = {"repository_version": repository_version_href}
        else:
            natural_key = {"repository_version": None}

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
