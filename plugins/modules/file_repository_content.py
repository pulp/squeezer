#!/usr/bin/python

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
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Add or remove content
  pulp.squeezer.file_repository_content:
    pulp_url: https://pulp.example.org
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


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpAnsibleModule

try:
    from pulp_glue.common.context import PulpException
    from pulp_glue.file.context import PulpFileContentContext, PulpFileRepositoryContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
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

        repository_ctx = PulpFileRepositoryContext(
            module.pulp_ctx, entity={"name": repository_name}
        )
        version_ctx = repository_ctx.get_version_context()
        version_ctx.entity = {"number": version}
        if version:
            repository_version_href = repository_ctx.entity["versions_href"] + "{version}/".format(
                version=version
            )
        else:
            repository_version_href = repository_ctx.entity["latest_version_href"]

        desired_present_content = module.params["present_content"]
        desired_absent_content = module.params["absent_content"]
        content_to_add = []
        content_to_remove = []

        if desired_present_content is not None:
            for item in desired_present_content:
                item.pop("digest", None)
                file_content_ctx = PulpFileContentContext(
                    module.pulp_ctx,
                    entity=item,
                )
                try:
                    file_content_ctx.find(repository_version=repository_version_href, **item)
                except PulpException:
                    content_to_add.append(file_content_ctx.entity["pulp_href"])

        if desired_absent_content is not None:
            for item in desired_absent_content:
                item.pop("digest", None)
                file_content_ctx = PulpFileContentContext(
                    module.pulp_ctx,
                    entity={"repository_version": repository_version_href, **item},
                )
                try:
                    content_to_remove.append(file_content_ctx.entity["pulp_href"])
                except PulpException:
                    pass

        if content_to_add or content_to_remove:
            if not module.check_mode:
                repository_version_href = repository_ctx.modify(
                    add_content=content_to_add,
                    remove_content=content_to_remove,
                    base_version=repository_version_href,
                )
            module.set_changed()

        module.set_result("content_added", content_to_add)
        module.set_result("content_removed", content_to_remove)
        module.set_result("repository_version", repository_version_href)


if __name__ == "__main__":
    main()
