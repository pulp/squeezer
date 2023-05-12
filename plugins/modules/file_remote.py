#!/usr/bin/python

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: file_remote
short_description: Manage file remotes of a pulp api server instance
description:
  - "This performs CRUD operations on file remotes in a pulp api server instance."
options:
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on_demand
      - streamed
extends_documentation_fragment:
  - pulp.squeezer.pulp.remote
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of file remotes from pulp api server
  pulp.squeezer.file_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: remote_status
- name: Report pulp file remotes
  debug:
    var: remote_status

- name: Create a file remote
  pulp.squeezer.file_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_file_remote
    url: http://localhost/pub/file/pulp_manifest
    state: present

- name: Delete a file remote
  pulp.squeezer.file_remote:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_file_remote
    state: absent
"""

RETURN = r"""
  remotes:
    description: List of file remotes
    type: list
    returned: when no name is given
  remote:
    description: File remote details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpRemoteAnsibleModule

try:
    from pulp_glue.file.context import PulpFileRemoteContext

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpFileRemoteContext = None


def main():
    with PulpRemoteAnsibleModule(
        context_class=PulpFileRemoteContext,
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            policy=dict(choices=["immediate", "on_demand", "streamed"]),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}

        module.process(natural_key, {})


if __name__ == "__main__":
    main()
