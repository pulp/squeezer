#!/usr/bin/python

# copyright (c) 2025, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: user
short_description: Manage users of a pulp api server instance
description:
  - "This performs CRUD operations on users in a pulp api server instance."
options:
  user:
    description:
      - User object to manipulate
    type: dict
    suboptions:
      username:
        description:
          - Username of the user to query or manipulate
        type: str
        required: true
      password:
        description:
          - Users password
        type: str
      first_name:
        description:
          - Users first name
        type: str
      last_name:
        description:
          - Users last name
        type: str
      email:
        description:
          - Users e-mail
        type: str
      is_active:
        description:
          - Whether the user can log in
        type: bool
      is_staff:
        description:
          - Whether the user belongs to the staff
          - This django attribute has no effect on pulp operations
        type: bool
extends_documentation_fragment:
  - pulp.squeezer.pulp.entity_state
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of users from pulp api server
  pulp.squeezer.user:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: users
- name: Report users
  debug:
    var: users
"""

RETURN = r"""
  users:
    description: List of x509 cert guards
    type: list
    returned: when no user is given
  user:
    description: user details
    type: dict
    returned: when user.username is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.core.context import PulpUserContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpUserContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpUserContext,
        entity_singular="user",
        entity_plural="users",
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "user": {
                "type": "dict",
                "options": {
                    "username": {"required": True},
                    "password": {"no_log": True},
                    "first_name": {},
                    "last_name": {},
                    "email": {},
                    "is_active": {"type": "bool"},
                    "is_staff": {"type": "bool"},
                },
            }
        },
        required_if=[("state", "present", ["user"]), ("state", "absent", ["user"])],
    ) as module:
        user = module.params["user"]
        natural_key = {"username": user and user["username"]}
        desired_attributes = {}
        if user is not None:
            for key, value in user.items():
                if key != "username" and value is not None:
                    desired_attributes[key] = value

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
