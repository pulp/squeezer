#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: repair
short_description: Repair corrupted artifacts in a repository version on a pulp server
description:
  - "Performes a repair task that identifies corrupted artifact files and attempts to refetch them."
options:
  repository:
    description:
      - Name of the repository to have a version repaired
    type: str
    required: true
  version:
    description:
      - Version number to be repaired
    type: int
    required: false
extends_documentation_fragment:
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Repair latest version of a repository
  repair:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
- name: Repair first version of a repository
  repair:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    version: 1
"""

RETURN = r"""
  corrupted:
    description: Number of identified corrupted artifacts
    type: int
    returned: if available
  missing:
    description: Number of identified missing artifacts
    type: int
    returned: if available
  repaired:
    description: Number of successfully repaired artifacts
    type: int
    returned: if available
"""

import re
import traceback
from contextlib import suppress
from importlib import import_module

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpAnsibleModule

try:
    from pulp_glue.common.context import PulpRepositoryContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
else:
    # TODO We need some mechanism for glue to pickup plugins automatically.
    for plugin in [
        "ansible",
        "container",
        "deb",
        "file",
        "gem",
        "maven",
        "ostree",
        "python",
        "rpm",
    ]:
        with suppress(ImportError):
            import_module(f"pulp_glue.{plugin}.context")


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        supports_check_mode=False,
        argument_spec=dict(
            repository=dict(required=True),
            version=dict(type="int"),
        ),
    ) as module:
        repository_ctx = PulpRepositoryContext(
            module.pulp_ctx, entity={"name": module.params["repository"]}
        )
        # "cast" to the proper subclass
        # TODO implement this in glue
        m = re.search(repository_ctx.HREF_PATTERN, repository_ctx.pulp_href)
        plugin = m.group("plugin")
        resource_type = m.group("resource_type")
        repository_ctx = PulpRepositoryContext.TYPE_REGISTRY[f"{plugin}:{resource_type}"](
            module.pulp_ctx, pulp_href=repository_ctx.pulp_href
        )
        # ----
        repository_version_ctx = repository_ctx.get_version_context()
        if module.params["version"] is None:
            repository_version_ctx.pulp_href = repository_ctx.entity["latest_version_href"]
        else:
            repository_version_ctx.entity = {"number": module.params["version"]}

        for report in repository_version_ctx.repair()["progress_reports"]:
            if report["code"] == "repair.corrupted":
                module.set_result("corrupted", report["done"])
            elif report["code"] == "repair.missing":
                module.set_result("missing", report["done"])
            elif report["code"] == "repair.repaired":
                module.set_result("repaired", report["done"])
            else:
                module.warn(f"Unknown report result '{report['code']}'.")


if __name__ == "__main__":
    main()
