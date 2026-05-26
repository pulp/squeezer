#!/usr/bin/python

# copyright (c) 2020, Jacob Floyd
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: rpm_repository
short_description: Manage rpm repositories of a pulp api server instance
description:
  - "This performs CRUD operations on rpm repositories in a pulp api server instance."
options:
  name:
    description:
      - A unique name of the repository to query or manipulate
      - Required for Create, Update, and Destroy operations
      - If no value is specified, returns a list of all repositories
    type: str
  description:
    description:
      - An optional description of the repository
    type: str
  autopublish:
    description:
      - Whether to automatically create publications for new repository versions
    type: bool
    version_added: "0.0.13"
  remote:
    description:
      - An optional remote to use by default when syncing
    type: str
    version_added: "0.0.16"
  repo_config:
    description:
      - A JSON document or data structure describing a config.repo file
    type: raw
    version_added: "0.0.16"
  retain_package_versions:
    description:
      - Max number of latest versions of each package to keep
    type: int
    version_added: "0.0.16"
  retain_repo_versions:
    description:
      - Max number of repository versions to keep
    type: int
    version_added: "0.0.16"
  pulp_labels:
    description:
      - A dictionary assigning pulp labels using string keys and values
    type: dict
    version_added: "0.4.0"
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Jacob Floyd (@cognifloyd)
  - Aaron Sweeney (@ajsween)
"""

EXAMPLES = r"""
- name: Read list of rpm repositories from pulp api server
  pulp.squeezer.rpm_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: repo_status
- name: Report pulp rpm repositories
  debug:
    var: repo_status

- name: Create a rpm repository
  pulp.squeezer.rpm_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    autopublish: true
    remote: existing_remote
    retain_package_versions: 3
    repo_config:
      gpgcheck: 1
    state: present

- name: Delete a rpm repository
  pulp.squeezer.rpm_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    state: absent
"""

RETURN = r"""
  repositories:
    description: List of rpm repositories
    type: list
    returned: when no name is given
  repository:
    description: Rpm repository details
    type: dict
    returned: when name is given
"""

import json
import traceback

from ansible.module_utils.six import string_types
from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.rpm.context import PulpRpmRemoteContext, PulpRpmRepositoryContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpRpmRepositoryContext = None

DESIRED_KEYS = {
    "autopublish",
    "description",
    "remote",
    "repo_config",
    "retain_package_versions",
    "retain_repo_versions",
    "pulp_labels",
}


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpRpmRepositoryContext,
        entity_singular="repository",
        entity_plural="repositories",
        argument_spec={
            "name": {},
            "description": {},
            "autopublish": {"type": "bool"},
            "remote": {},
            "repo_config": {"type": "raw"},
            "retain_package_versions": {"type": "int"},
            "retain_repo_versions": {"type": "int"},
            "pulp_labels": {"type": "dict"},
        },
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        remote_name = module.params["remote"]
        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in DESIRED_KEYS if module.params[key] is not None
        }

        if remote_name is not None:
            if remote_name:
                remote_ctx = PulpRpmRemoteContext(module.pulp_ctx, entity={"name": remote_name})
                desired_attributes["remote"] = remote_ctx.pulp_href
            else:
                desired_attributes["remote"] = ""

        # Encode the repo_config unless its a string, then assume it is pre-formatted JSON
        if "repo_config" in desired_attributes and isinstance(
            desired_attributes["repo_config"], string_types
        ):
            desired_attributes["repo_config"] = json.loads(desired_attributes["repo_config"])

        # Ensure `pulp_labels` contains only strings for keys and values
        if "pulp_labels" in desired_attributes:
            labels = desired_attributes["pulp_labels"]
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in labels.items()):
                module.fail_json(
                    msg="pulp_labels must be a dictionary with strings as keys and values"
                )

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
