# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    # Common pulp documentation fragment
    DOCUMENTATION = r"""
options:
  pulp_url:
    description:
      - URL of the server to connect to (without 'pulp/api/v3').
      - If no value is specified, the value of the environment variable C(SQUEEZER_PULP_URL) will be used as a fallback.
    type: str
    required: true
  username:
    description:
      - Username of api user.
      - If no value is specified, the value of the environment variable C(SQUEEZER_USERNAME) will be used as a fallback.
    type: str
    required: true
  password:
    description:
      - Password of api user.
      - If no value is specified, the value of the environment variable C(SQUEEZER_PASSWORD) will be used as a fallback.
    type: str
    required: true
  validate_certs:
    description:
      - Whether SSL certificates should be verified.
      - If no value is specified, the value of the environment variable C(SQUEEZER_VALIDATE_CERTS) will be used as a fallback.
    type: bool
    default: true
  refresh_api_cache:
    description:
      - Whether the cached API specification should be invalidated.
      - It is recommended to use this once with the M(pulp.squeezer.status) module at the beginning of the playbook.
    type: bool
    default: false
"""

    ENTITY_STATE = r"""
options:
  state:
    description:
      - State the entity should be in
    type: str
    choices:
      - present
      - absent
"""
