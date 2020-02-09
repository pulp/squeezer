# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Common pulp documentation fragment
    DOCUMENTATION = r'''
requires:
  - pulpcore-client
options:
  api_url:
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
    choices:
      - present
      - absent
'''
