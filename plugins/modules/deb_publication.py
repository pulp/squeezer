#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


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
    choices: ["structured", "simple", "simple_and_structured", "verbatim"]
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of deb publications
  pulp.squeezer.deb_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: publication_status
- name: Report pulp deb publications
  debug:
    var: publication_status

- name: Create a deb publication
  pulp.squeezer.deb_publication:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: my_deb_repo
    state: present

- name: Delete a deb publication
  pulp.squeezer.deb_publication:
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


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    GLUE_DEB_VERSION_SPEC,
    PulpEntityAnsibleModule,
    assert_version,
)

try:
    from pulp_glue.deb import __version__ as pulp_glue_deb_version
    from pulp_glue.deb.context import (
        PulpAptPublicationContext,
        PulpAptRepositoryContext,
        PulpVerbatimPublicationContext,
    )

    assert_version(GLUE_DEB_VERSION_SPEC, pulp_glue_deb_version, "pulp-glue-deb")
    PULP_GLUE_DEB_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_DEB_IMPORT_ERR = traceback.format_exc()
    PulpAptPublicationContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpAptPublicationContext,
        entity_singular="publication",
        entity_plural="publications",
        import_errors=[("pulp-glue-deb", PULP_GLUE_DEB_IMPORT_ERR)],
        argument_spec={
            "repository": {},
            "version": {"type": "int"},
            "mode": {
                "choices": ["structured", "simple", "simple_and_structured", "verbatim"],
            },
        },
        required_if=(
            ["state", "present", ["repository"]],
            ["state", "absent", ["repository"]],
        ),
    ) as module:
        repository_name = module.params["repository"]
        version = module.params["version"]
        mode = module.params["mode"]

        desired_attributes = {}
        if mode is not None:
            if mode == "verbatim":
                # A bit of a hack. We need to change the publication context class.
                module.context = PulpVerbatimPublicationContext(module.pulp_ctx)
            else:
                desired_attributes = {
                    "simple": "simple" in mode,
                    "structured": "structured" in mode,
                }

        if repository_name:
            repository_ctx = PulpAptRepositoryContext(
                module.pulp_ctx, entity={"name": repository_name}
            )
            # TODO check if version exists
            if version:
                repository_version_href = repository_ctx.entity["versions_href"] + f"{version}/"
            else:
                repository_version_href = repository_ctx.entity["latest_version_href"]
            natural_key = {"repository_version": repository_version_href}
        else:
            natural_key = {"repository_version": None}

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
