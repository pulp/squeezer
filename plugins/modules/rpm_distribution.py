#!/usr/bin/python


# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: rpm_distribution
short_description: Manage rpm distributions of a pulp api server instance
description:
  - "This performs CRUD operations on rpm distributions in a pulp api server instance."
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
  repository:
    description:
      - Name of the repository to be served
    type: str
    required: false
    version_added: "0.0.15"
  content_guard:
    description:
      - Name of the content guard for the served content
      - "Warning: This feature is not yet supported."
    type: str
    required: false
  generate_repo_config:
    description:
      - Specify whether Pulp should generate *.repo files
    type: bool
    required: false
    version_added: "0.0.16"
  pulp_labels:
    description:
      - Labels consisting of key, value pairs
    type: dict
    required: false
    version_added: "0.0.16"
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Jacob Floyd (@cognifloyd)
"""

EXAMPLES = r"""
- name: Read list of rpm distributions
  pulp.squeezer.rpm_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: distribution_status
- name: Report pulp rpm distributions
  debug:
    var: distribution_status

- name: Create a rpm distribution
  pulp.squeezer.rpm_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_rpm_distribution
    base_path: new/rpm/dist
    publication: /pub/api/v3/publications/rpm/rpm/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/
    generate_repo_config: true
    state: present

- name: Delete a rpm distribution
  pulp.squeezer.rpm_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_rpm_distribution
    state: absent

- name: Add a rpm distribution label
  pulp.squeezer.rpm_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_rpm_distribution
    pulp_label:
      key1: value1
"""

RETURN = r"""
  distributions:
    description: List of rpm distributions
    type: list
    returned: when no name is given
  distribution:
    description: Rpm distribution details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.core.context import PulpContentGuardContext
    from pulp_glue.rpm.context import PulpRpmDistributionContext, PulpRpmRepositoryContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpRpmDistributionContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpRpmDistributionContext,
        entity_singular="distribution",
        entity_plural="distributions",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "name": {},
            "base_path": {},
            "publication": {},
            "repository": {},
            "content_guard": {},
            "generate_repo_config": {"type": "bool"},
            "pulp_labels": {"type": "dict"},
        },
        required_if=[
            ("state", "present", ["name", "base_path"]),
            ("state", "absent", ["name"]),
        ],
        mutually_exclusive=[("publication", "repository")],
    ) as module:
        content_guard_name = module.params["content_guard"]
        repository_name = module.params["repository"]

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in [
                "base_path",
                "generate_repo_config",
                "publication",
                "pulp_labels",
            ]
            if module.params[key] is not None
        }

        if repository_name is not None:
            if repository_name:
                repository_ctx = PulpRpmRepositoryContext(
                    module.pulp_ctx, entity={"name": repository_name}
                )
                desired_attributes["repository"] = repository_ctx.pulp_href
            else:
                desired_attributes["repository"] = ""

        if content_guard_name is not None:
            if content_guard_name:
                content_guard_ctx = PulpContentGuardContext(
                    module.pulp_ctx, entity={"name": content_guard_name}
                )
                desired_attributes["content_guard"] = content_guard_ctx.pulp_href
            else:
                desired_attributes["content_guard"] = ""

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
