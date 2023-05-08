#!/usr/bin/python
# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: x509_cert_guard
short_description: Manage x509 cert guards of a pulp api server instance
description:
  - "This performs CRUD operations on x509 cert guards in a pulp api server instance."
options:
  name:
    description:
      - Name of the cert guard to query or manipulate
    type: str
  description:
    description:
      - Description of the cert guard
    type: str
  ca_certificate:
    description:
      - The Certificate Authority (CA) certificate
    type: str
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Matthias Dellweg (@mdellweg)
"""

EXAMPLES = r"""
- name: Read list of x509 cert guards from pulp api server
  pulp.squeezer.x509_cert_guard:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
  register: guard_status
- name: Report pulp x509 cert guards
  debug:
    var: guard_status

- name: Create a x509 cert guard
  pulp.squeezer.x509_cert_guard:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_cert_guard
    description: A brand new cert guard with a description
    ca_certificate: "{{ lookup('file', path_to_ca_cert) }}"
    state: present

- name: Delete a x509 cert guard
  pulp.squeezer.x509_cert_guard:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    name: new_cert_guard
    state: absent
"""

RETURN = r"""
  cert_guards:
    description: List of x509 cert guards
    type: list
    returned: when no name is given
  cert_guard:
    description: x509 cert guard details
    type: dict
    returned: when name is given
"""


import traceback

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpEntityAnsibleModule

try:
    from pulp_glue.core.context import PulpContentGuardContext

    class PulpX509CertGuardContext(PulpContentGuardContext):
        ID_PREFIX = "contentguards_certguard_x509"
        HREF = "certguard_x509_cert_guard_href"
        NULLABLES = {"description"}

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
    PulpX509CertGuardContext = None


def main():
    with PulpEntityAnsibleModule(
        context_class=PulpX509CertGuardContext,
        entity_singular="content_guard",
        entity_plural="content_guards",
        import_errors=[("pulp-glue", PULP_CLI_IMPORT_ERR)],
        argument_spec=dict(
            name=dict(),
            description=dict(),
            ca_certificate=dict(),
        ),
        required_if=[("state", "present", ["name"]), ("state", "absent", ["name"])],
    ) as module:
        natural_key = {"name": module.params["name"]}
        desired_attributes = {}
        if module.params["description"] is not None:
            # In case of an empty string we nullify the description
            desired_attributes["description"] = module.params["description"]
        if module.params["ca_certificate"] is not None:
            desired_attributes["ca_certificate"] = module.params["ca_certificate"]

        module.process(natural_key, desired_attributes)


if __name__ == "__main__":
    main()
