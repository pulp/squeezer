# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
---
module: pulp_artifact
short_description: Manage artifacts of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRD operations on artifacts in a pulp api server instance."
options:
  file:
    description:
      - A local file that should be turned into an artifact.
    type: path
  sha256:
    description:
      - sha256 digest of the artifact to query or delete.
      - When specified together with file, it will be used to verify any transaction.
    type: str
  state:
    description:
      - State the artifact should be in
    choices:
      - present
      - absent
extends_documentation_fragment:
  - pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of artifacts from pulp server
  pulp_artifact:
    api_url: localhost:24817
    username: admin
    password: password
  register: artifact_status
- name: Report pulp artifacts
  debug:
    var: artifact_status
- name: Upload a file
  pulp_artifact:
    api_url: localhost:24817
    username: admin
    password: password
    file: local_artifact.txt
    state: present
- name: Delete an artifact by specifying a file
  pulp_atifact:
    api_url: localhost:24817
    username: admin
    password: password
    file: local_artifact.txt
    state: absent
- name: Delete an artifact by specifying the digest
  pulp_atifact:
    api_url: localhost:24817
    username: admin
    password: password
    sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    state: absent
'''

RETURN = r'''
  artifacts:
    description: List of artifacts
    type: list
    return: when no file or sha256 is given
  artifact:
    description: Artifact details
    type: dict
    return: when file or sha256 is given
'''


from ansible.module_utils.pulp_helper import PulpEntityAnsibleModule


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            file=dict(),
            sha256=dict(),
        ),
        required_if=[
            ('state', 'present', ['file']),
        ],
        entity_name='artifact',
        entity_plural='artifacts',
    )

    sha256 = module.params['sha256']
    if module.params['file']:
        file_sha256 = module.sha256(module.params['file'])
        if sha256:
            if sha256 != file_sha256:
                module.fail_json(msg="File checksum mismatch.")
        else:
            sha256 = file_sha256

    if sha256 is None and module.params['state'] == 'absent':
        module.fail_json(msg="One of 'file' and 'sha256' is required if 'state' is 'absent'.")

    natural_key = {
        'sha256': sha256,
    }
    desired_attributes = {
        'file': module.params['file'],
    }

    module.process_entity(natural_key, desired_attributes)


if __name__ == '__main__':
    main()
