#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: task
short_description: Manage tasks of a pulp api server instance
description:
  - "This performs list, show and cancel operations on tasks in a pulp server."
options:
  pulp_href:
    description:
      - Pulp reference of the task to query or manipulate
    type: str
  state:
    description:
      - Desired state of the task.
    type: str
    choices:
      - absent
      - canceled
      - completed
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of tasks from pulp server
  tasks:
    api_url: localhost:24817
    username: admin
    password: password
  register: task_summary
- name: Report pulp tasks
  debug:
    var: task_summary
# TODO
- name: Create a file remote
  file_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_file_remote
    url: http://localhost/pub/file/pulp_manifest
    state: present
- name: Delete a file remote
  file_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_file_remote
    state: absent
"""

RETURN = r"""
  tasks:
    description: List of tasks
    type: list
    returned: when no id is given
  remote:
    description: Task details
    type: dict
    returned: when id is given
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PulpEntityAnsibleModule,
    PulpTask,
)


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            pulp_href=dict(),
            state=dict(
                choices=["absent", "canceled", "completed"],
            ),
        ),
        required_if=[
            ("state", "absent", ["pulp_href"]),
            ("state", "canceled", ["pulp_href"]),
            ("state", "completed", ["pulp_href"]),
        ],
    ) as module:

        natural_key = {"pulp_href": module.params["pulp_href"]}
        desired_attributes = {}

        PulpTask(module, natural_key, desired_attributes).process()


if __name__ == "__main__":
    main()
