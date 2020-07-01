#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: pulp_status
short_description: Report status of a pulp api server instance
description:
  - "This module queries a pulp api server instance for installed plugins and service connectivity."
options: {}
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read status from pulp api server
  pulp_status:
    api_url: localhost:24817
    username: admin
    password: password
  register: pulp_status
- name: Report pulp status
  debug:
    var: pulp_status
'''

RETURN = r'''
  status:
    description: Pulp server status
    type: dict
    returned: always
'''


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_helper import (
    PulpAnsibleModule,
    PulpStatus,
)


def main():
    with PulpAnsibleModule() as module:
        status = PulpStatus(module).api.status_read()
        module.set_result('status', status.to_dict())


if __name__ == '__main__':
    main()
