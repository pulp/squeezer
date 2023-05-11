#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: status
short_description: Report status of a pulp api server instance
description:
  - "This module queries a pulp api server instance for installed plugins and service connectivity."
options: {}
extends_documentation_fragment:
  - pulp.squeezer.pulp.glue
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read status from pulp api server
  pulp.squeezer.status:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: pulp_status
- name: Report pulp status
  debug:
    var: pulp_status
"""

RETURN = r"""
  status:
    description: Pulp server status
    type: dict
    returned: always
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpAnsibleModule


def main():
    with PulpAnsibleModule(no_auth=True) as module:
        result = module.pulp_ctx.call("status_read")
        # verify cached api doc against server versions
        component_versions = {
            item["component"]: item["version"] for item in result.get("versions", [])
        }
        if component_versions != module.pulp_ctx.component_versions:
            module.warn("Notice: Cached api is outdated. Refreshing...")
            module.pulp_ctx.api.load_api(refresh_cache=True)
            result = module.pulp_ctx.call("status_read")
        module.set_result("status", result)


if __name__ == "__main__":
    main()
