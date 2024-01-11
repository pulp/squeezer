#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: ansible_distribution
short_description: Manage ansible distributions of a pulp server
description:
  - "This performs CRUD operations on ansible distributions in a pulp server."
options:
  name:
    description:
      - Name of the distribution to query or manipulate
    type: str
    required: false
  base_path:
    description:
      - Base path to distribute a repository
    type: str
    required: false
  repository:
    description:
      - Name of the repository to be served
    type: str
    required: false
  version:
    description:
      - Version number of the repository to be served
      - If not specified, the distribution will always serve the latest version.
    type: int
    required: false
  content_guard:
    description:
      - Name of the content guard for the served content
      - Or the empty string to remove the content guard
    type: str
    required: false
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of ansible distributions from pulp api server
  pulp.squeezer.ansible_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: distribution_status
- name: Report pulp ansible distributions
  debug:
    var: distribution_status

- name: Create an ansible distribution
  pulp.squeezer.ansible_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ansible_distribution
    base_path: new/ansible/dist
    repository: my_repository
    state: present

- name: Delete an ansible distribution
  pulp.squeezer.ansible_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_ansible_distribution
    state: absent
"""

RETURN = r"""
  distributions:
    description: List of ansible distributions
    type: list
    returned: when no name is given
  distribution:
    description: Ansible distribution details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.ansible.context import (
        PulpAnsibleDistributionContext,
        PulpAnsibleRepositoryContext,
    )
    from pulp_glue.core.context import PulpContentGuardContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpAnsibleDistributionContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpAnsibleDistributionContext,
        entity_singular="distribution",
        entity_plural="distribuions",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            name=dict(),
            base_path=dict(),
            repository=dict(),
            version=dict(type="int"),
            content_guard=dict(),
        ),
        required_if=[
            ("state", "present", ["name", "base_path"]),
            ("state", "absent", ["name"]),
        ],
    ) as module:
        repository_name = module.params["repository"]
        version = module.params["version"]
        content_guard_name = module.params["content_guard"]

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key] for key in ["base_path"] if module.params[key] is not None
        }

        if repository_name:
            repository_ctx = PulpAnsibleRepositoryContext(
                module.pulp_ctx, entity={"name": repository_name}
            )
            if version:
                desired_attributes["repository_version"] = (
                    repository_ctx.entity["versions_href"] + f"{version}/"
                )
            else:
                desired_attributes["repository"] = repository_ctx.pulp_href

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
