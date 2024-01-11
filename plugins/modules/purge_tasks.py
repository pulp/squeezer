#!/usr/bin/python

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: purge_tasks
short_description: Purge finished tasks
description:
  - "Purge tasks in specific finished states with a certain minimal age."
options:
  finished_before:
    description:
      - Datetime to specify the least age of tasks to purge.
    type: str
  states:
    description:
      - Pulp reference of the task to query or manipulate
    type: list
    elements: str
    choices:
      - canceled
      - completed
      - failed
extends_documentation_fragment:
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Remove old finished tasks
  pulp.squeezer.purge_tasks:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: task_purge_summary
- name: Report removed tasks
  debug:
    var: task_purge_summary
"""

RETURN = r"""
  summary:
    description: Task purge details
    type: dict
    returned: always
"""


import traceback
from datetime import datetime

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpAnsibleModule

try:
    from pulp_glue.core.context import PulpTaskContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()


def main():
    with PulpAnsibleModule(
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            finished_before=dict(),
            states=dict(
                type="list",
                elements="str",
                choices=["canceled", "completed", "failed"],
            ),
        ),
    ) as module:
        task_ctx = PulpTaskContext(module.pulp_ctx)
        summary = {"objects": {}, "total": 0, "errors": 0}
        finished_before = module.params["finished_before"]
        if finished_before is not None:
            finished_before = datetime.fromisoformat(finished_before)
        if not module.check_mode:
            purge_task = task_ctx.purge(
                finished_before=finished_before, states=module.params["states"]
            )
            for report in purge_task["progress_reports"]:
                if report["code"] == "purge.tasks.total":
                    summary["total"] = report["total"]
                elif report["code"] == "purge.tasks.error":
                    summary["errors"] = report["total"]
                elif report["code"].startswith("purge.tasks.key"):
                    summary["objects"][report["code"][16:]] = report["total"]
        module.set_changed()
        module.set_result("summary", summary)


if __name__ == "__main__":
    main()
