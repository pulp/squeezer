#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: file_repository_content
short_description: Manage content in file repositories of a pulp server
description:
  - "This module adds or removes content to/from file repositories in a pulp server."
options:
  repository:
    description:
      - Name of the repository to manipulate
    type: str
    required: true
  base_version:
    description:
      - Number of the version to use as the base of operations
    type: int
  present_content:
    description:
      - List of content to be present in the latest repositroy version
    type: list
    elements: dict
    suboptions:
      relative_path:
        description:
          - Relative path of the content unit
        type: str
        required: true
      sha256:
        aliases:
          - digest
        description:
          - SHA256 digest of the content unit
        type: str
        required: true
  absent_content:
    description:
      - List of content to be absent in the latest repositroy version
    type: list
    elements: dict
    suboptions:
      relative_path:
        description:
          - Relative path of the content unit
        type: str
        required: true
      sha256:
        aliases:
          - digest
        description:
          - SHA256 digest of the content unit
        type: str
        required: true
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Add or remove content
  file_repository_content:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_repo
    present_content:
      - relative_path: file/to/be/present
        sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    absent_content:
      - relative_path: file/to/be/absent
        sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
"""

RETURN = r"""
  repository_version:
    description: Href of the repository version found or created
    type: str
    returned: always
  content_added:
    description: List of content unit hrefs that were added
    type: list
    returned: always
  content_removed:
    description: List of content unit hrefs that were removed
    type: list
    returned: always
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpAnsibleModule,
    PulpFileContent,
    PulpFileRepository,
)


def main():
    with PulpAnsibleModule(
        argument_spec=dict(
            repository=dict(required=True),
            base_version=dict(type="int"),
            present_content=dict(
                type="list",
                elements="dict",
                options=dict(
                    relative_path=dict(required=True),
                    sha256=dict(required=True, aliases=["digest"]),
                ),
            ),
            absent_content=dict(
                type="list",
                elements="dict",
                options=dict(
                    relative_path=dict(required=True),
                    sha256=dict(required=True, aliases=["digest"]),
                ),
            ),
        ),
    ) as module:

        repository_name = module.params["repository"]
        version = module.params["base_version"]

        repository = PulpFileRepository(module, {"name": repository_name})
        repository.find(failsafe=False)
        # TODO check if version exists
        if version:
            repository_version_href = repository.entity[
                "versions_href"
            ] + "{version}/".format(version=version)
        else:
            repository_version_href = repository.entity["latest_version_href"]

        desired_present_content = module.params["present_content"]
        desired_absent_content = module.params["absent_content"]
        content_to_add = []
        content_to_remove = []

        if desired_present_content is not None:
            for item in desired_present_content:
                file_content = PulpFileContent(
                    module,
                    natural_key={
                        k: v
                        for k, v in item.items()
                        if k in ["sha256", "relative_path"]
                    },
                )
                file_content.find(
                    parameters={"repository_version": repository_version_href}
                )
                if file_content.entity is None:
                    file_content.find(failsafe=False)
                    content_to_add.append(file_content.entity["pulp_href"])

        if desired_absent_content is not None:
            for item in desired_absent_content:
                file_content = PulpFileContent(
                    module,
                    natural_key={
                        k: v
                        for k, v in item.items()
                        if k in ["sha256", "relative_path"]
                    },
                )
                file_content.find(
                    parameters={"repository_version": repository_version_href}
                )
                if file_content.entity is not None:
                    content_to_remove.append(file_content.entity["pulp_href"])

        if content_to_add or content_to_remove:
            repository_version_href = repository.modify(
                content_to_add, content_to_remove, repository_version_href
            )

        module.set_result("content_added", content_to_add)
        module.set_result("content_removed", content_to_remove)
        module.set_result("repository_version", repository_version_href)


if __name__ == "__main__":
    main()
