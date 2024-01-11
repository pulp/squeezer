#!/usr/bin/python

# copyright (c) 2021, Mark Goddard
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: container_distribution
short_description: Manage container distributions of a pulp api server instance
description:
  - "This performs CRUD operations on container distributions in a pulp api server instance."
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
      - The latest RepositoryVersion for this Repository will be served.
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
      - "Warning: This feature is not yet supported."
    type: str
    required: false
  private:
    description:
      - Whether to make the distribution private.
    type: bool
    required: false
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Mark Goddard (@markgoddard)
"""

EXAMPLES = r"""
- name: Read list of container distributions
  pulp.squeezer.container_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: distribution_status
- name: Report pulp container distributions
  debug:
    var: distribution_status

- name: Create a container distribution
  pulp.squeezer.container_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_container_distribution
    base_path: new/container/dist
    repository: repository
    state: present

- name: Delete a container distribution
  pulp.squeezer.container_distribution:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_container_distribution
    state: absent
"""

RETURN = r"""
  distributions:
    description: List of container distributions
    type: list
    returned: when no name is given
  distribution:
    description: Container distribution details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.container.context import (
        PulpContainerDistributionContext,
        PulpContainerRepositoryContext,
    )
    from pulp_glue.core.context import PulpContentGuardContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpContainerDistributionContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpContainerDistributionContext,
        entity_singular="distribution",
        entity_plural="distribuions",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            name=dict(),
            base_path=dict(),
            repository=dict(),
            version=dict(type="int"),
            content_guard=dict(),
            private=dict(type="bool"),
        ),
        required_if=[
            ("state", "present", ["name", "base_path"]),
            ("state", "absent", ["name"]),
        ],
    ) as module:
        repository_name = module.params["repository"]
        version = module.params["version"]
        content_guard_name = module.params["content_guard"]
        private = module.params["private"]

        natural_key = {"name": module.params["name"]}
        desired_attributes = {
            key: module.params[key]
            for key in ["base_path", "private"]
            if module.params[key] is not None
        }

        if repository_name:
            repository_ctx = PulpContainerRepositoryContext(
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
