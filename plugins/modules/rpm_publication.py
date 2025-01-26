#!/usr/bin/python

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: rpm_publication
short_description: Manage rpm publications of a pulp api server instance
description:
  - "This performs CRUD operations on rpm publications in a pulp api server instance."
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
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Jacob Floyd (@cognifloyd)
"""

EXAMPLES = r"""
- name: Read list of rpm publications
  pulp.squeezer.rpm_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: publication_status
- name: Report pulp rpm publications
  debug:
    var: publication_status

- name: Create a rpm publication
  pulp.squeezer.rpm_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: my_rpm_repo
    state: present

- name: Delete a rpm publication
  pulp.squeezer.rpm_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: my_rpm_repo
    state: absent
"""

RETURN = r"""
  publications:
    description: List of rpm publications
    type: list
    returned: when no repository is given
  publication:
    description: Rpm publication details
    type: dict
    returned: when repository is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.rpm.context import PulpRpmPublicationContext, PulpRpmRepositoryContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpRpmPublicationContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpRpmPublicationContext,
        entity_singular="publication",
        entity_plural="publications",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "repository": {},
            "version": {"type": "int"},
        },
        required_if=(
            ["state", "present", ["repository"]],
            ["state", "absent", ["repository"]],
        ),
    ) as module:
        repository_name = module.params["repository"]
        version = module.params["version"]
        desired_attributes = {}

        if repository_name:
            repository_ctx = PulpRpmRepositoryContext(
                module.pulp_ctx, entity={"name": repository_name}
            )
            # TODO check if version exists
            if version:
                repository_version_href = repository_ctx.entity[
                    "versions_href"
                ] + "{version}/".format(version=version)
            else:
                repository_version_href = repository_ctx.entity["latest_version_href"]
            natural_key = {"repository_version": repository_version_href}
        else:
            natural_key = {"repository_version": None}

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
