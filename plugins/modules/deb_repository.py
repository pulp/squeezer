#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: deb_repository
short_description: Manage deb repositories of a pulp api server instance
description:
  - "This performs CRUD operations on deb repositories in a pulp api server instance."
options:
  name:
    description:
      - Name of the repository to query or manipulate
    type: str
  description:
    description:
      - Description of the repository
    type: str
  remote:
    description:
      - An optional remote to use by default when syncing
    type: str
  pulp_labels:
    description:
      - A dictionary assigning pulp labels using strings for keys and values
    type: dict
    version_added: "0.4.0"
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of deb repositories from pulp api server
  pulp.squeezer.deb_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: repo_status
- name: Report pulp deb repositories
  debug:
    var: repo_status

- name: Create a deb repository
  pulp.squeezer.deb_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    description: A brand new repository with a description
    state: present

- name: Create a deb repository with a default remote set
  pulp.squeezer.deb_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo_with_remote
    description: A brand new repository with a remote set
    remote: my_remote
    state: present

- name: Delete a deb repository
  pulp.squeezer.deb_repository:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_repo
    state: absent
"""

RETURN = r"""
  repositories:
    description: List of deb repositories
    type: list
    returned: when no name is given
  repository:
    description: Deb repository details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import (
    GLUE_DEB_VERSION_SPEC,
    PulpEntityAnsibleModule,
    assert_version,
)

try:
    from pulp_glue.deb import __version__ as pulp_glue_deb_version
    from pulp_glue.deb.context import PulpAptRemoteContext, PulpAptRepositoryContext

    # In pulp-glue <0.35 this is needed for idempotent removal of the remote.
    PulpAptRepositoryContext.NULLABLES.add("remote")

    assert_version(GLUE_DEB_VERSION_SPEC, pulp_glue_deb_version, "pulp-glue-deb")
    PULP_GLUE_DEB_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_DEB_IMPORT_ERR = traceback.format_exc()
    PulpAptRepositoryContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpAptRepositoryContext,
        entity_singular="repository",
        entity_plural="repositories",
        import_errors=[("pulp-glue-deb", PULP_GLUE_DEB_IMPORT_ERR)],
        argument_spec={
            "name": {},
            "description": {},
            "remote": {},
            "pulp_labels": {"type": "dict"},
        },
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        remote_name = module.params["remote"]
        natural_key = {"name": module.params["name"]}
        desired_attributes = {}

        if remote_name is not None:
            if remote_name:
                remote_ctx = PulpAptRemoteContext(module.pulp_ctx, entity={"name": remote_name})
                desired_attributes["remote"] = remote_ctx.pulp_href
            else:
                desired_attributes["remote"] = ""

        if module.params["description"] is not None:
            desired_attributes["description"] = module.params["description"]

        if module.params["pulp_labels"] is not None:
            labels = module.params["pulp_labels"]

            # Ensure `pulp_labels` contains only strings for keys and values
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in labels.items()):
                module.fail_json(
                    msg="pulp_labels must be a dictionary with strings as keys and values"
                )
            desired_attributes["pulp_labels"] = labels

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
