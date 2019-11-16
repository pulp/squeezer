# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # Common pulp documentation fragment
    DOCUMENTATION = r'''
requirements:
  - pulpcore-client
options:
  pulp_url:
    description:
      - URL of the server to connect to (without 'pulp/api/v3').
    type: str
    required: true
  username:
    description:
      - Username of api user.
    type: str
    required: true
  password:
    description:
      - Password of api user.
    type: str
    required: true
  validate_certs:
    description:
      - Whether SSL certificates should be verified.
    type: bool
    default: true
'''

    ENTITY_STATE = r'''
options:
  state:
    description:
      - State the entity should be in
    type: str
    choices:
      - present
      - absent
'''
