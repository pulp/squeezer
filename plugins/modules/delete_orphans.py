#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: delete_orphans
short_description: Deletes all orphaned entities of a pulp server
description:
  - "This module deletes all orphaned artifacts and content units of a pulp server."
options:
  protection_time:
    description: |
      How long in minutes Pulp should hold orphan Content and Artifacts before becoming candidates
      for cleanup task
    type: int
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Delete orphans
  pulp.squeezer.delete_orphans:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
"""

RETURN = r"""
  summary:
    description: Summary of deleted entities
    type: dict
    returned: always
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpAnsibleModule

try:
    from pulp_glue.core.context import PulpOrphanContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpTaskContext = None


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            protection_time=dict(type="int"),
        ),
    ) as module:
        if not module.check_mode:
            body = {}
            protection_time = module.params.get("protection_time")
            if protection_time is not None:
                body["orphan_protection_time"] = protection_time
            task = PulpOrphanContext(module.pulp_ctx).cleanup(body=body)
            summary = {
                item["message"].split(" ")[-1].lower(): item["total"]
                for item in task["progress_reports"]
            }
        else:
            # Fake it
            summary = {
                "artifacts": 0,
                "content": 0,
            }
        module.set_changed()
        module.set_result("summary", summary)


if __name__ == "__main__":
    main()
