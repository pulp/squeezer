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

    GLUE = r"""
options:
  username:
    required: false
  password:
    required: false
  user_cert:
    description:
      - Client certificate of api user.
    type: str
    required: false
  user_key:
    description:
      - Client certificate key of api user.
    type: str
    required: false
  timeout:
    description:
      - Time in seconds to wait for tasks.
    type: int
    default: 10
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

    READONLY_ENTITY_STATE = r"""
options:
  state:
    description:
      - State the entity should be in
    type: str
    choices:
      - present
"""

    REMOTE = r"""
options:
  name:
    description:
      - Name of the remote to query or manipulate
    type: str
  url:
    description:
      - URL to the upstream repository
    type: str
  remote_username:
    description:
      - The username to authenticate with the remote repository.
      - Using this parameter will always report C(changed=true).
    type: str
  remote_password:
    description:
      - The password to authenticate with the remote repository.
      - Using this parameter will always report C(changed=true).
    type: str
  ca_cert:
    description:
      - Certificate autority to identify the remote repository.
    type: str
  client_cert:
    description:
      - Client certificate to authenticate with the remote repository.
    type: str
  client_key:
    description:
      - Client key to authenticate with the remote repository.
      - Using this parameter will always report C(changed=true).
    type: str
  tls_validation:
    description:
      - If True, TLS peer validation must be performed on remote synchronization.
    type: bool
  proxy_url:
    description:
      - The proxy URL. Format C(scheme://host:port) .
    type: str
  proxy_username:
    description:
      - The username to authenticate with the proxy.
      - Using this parameter will always report C(changed=true).
    type: str
  proxy_password:
    description:
      - The password to authenticate with the proxy.
      - Using this parameter will always report C(changed=true).
    type: str
  download_concurrency:
    description:
      - Total number of simultaneous connections. If not set then the default value will be used.
    type: int
  rate_limit:
    description:
      - Limits requests per second for each concurrent downloader.
    type: int
  total_timeout:
    description:
      - C(aiohttp.ClientTimeout.total) for download-connections. The default is null, which will cause the default from the aiohttp library to be used.
    type: float
  connect_timeout:
    description:
      - C(aiohttp.ClientTimeout.connect) for download-connections. The default is null, which will cause the default from the aiohttp library to be used.
    type: float
  sock_connect_timeout:
    description:
      - C(aiohttp.ClientTimeout.sock_connect) for download-connections. The default is null, which will cause the default from the aiohttp library to be used.
    type: float
  sock_read_timeout:
    description:
      - C(aiohttp.ClientTimeout.sock_read) for download-connections. The default is null, which will cause the default from the aiohttp library to be used.
    type: float
  max_retries:
    description:
      - Maximum number of retry attempts after a download failure. If not set then the default value (3) will be used.
    type: int
"""
