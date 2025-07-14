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
      groups:
        description:
          - List of groups the user should be in
        type: list
        elements: str
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
    description: List of users
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
    from pulp_glue.core.context import PulpGroupContext, PulpGroupUserContext, PulpUserContext

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpUserContext = None
    PulpGroupContext = None
    PulpGroupUserContext = None


class PulpUserAnsibleModule(PulpEntityAnsibleModule):
    def process_converge(self, desired_entity, defaults=None):
        # Ideally glue would do this for us...
        groups = desired_entity and desired_entity.pop("groups", None)
        changed, before, after = super().process_converge(desired_entity, defaults=defaults)
        if self.check_mode and after is not None:
            # Fake the groups.
            after.setdefault("groups", [])
        if groups is not None:
            desired_groups = set(groups)
            actual_groups = {g["name"] for g in after["groups"]}
            missing_groups = desired_groups - actual_groups
            superfluous_groups = actual_groups - desired_groups
            for group in missing_groups:
                group_ctx = PulpGroupContext(self.pulp_ctx, entity={"name": group})
                # Apparently pulp_glue did never implement this.
                # group_ctx.add_user(after["username"])
                # ---8<--- Workaround ----8<----
                group_user_ctx = PulpGroupUserContext(self.pulp_ctx, group_ctx)
                group_user_ctx.create(body={"username": self.context.entity["username"]})
                # ---8<-------8<----
                after["groups"].append(group_ctx.entity)
                changed = True
            for group in superfluous_groups:
                group_ctx = PulpGroupContext(self.pulp_ctx, entity={"name": group})
                group_ctx.remove_user(self.context)
                after["groups"] = [g for g in after["groups"] if g["name"] != group]
                changed = True

        return changed, before, after


def main():
    with PulpUserAnsibleModule(
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
                    "groups": {"type": "list", "elements": "str"},
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
                if key not in ["username"] and value is not None:
                    desired_attributes[key] = value

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
