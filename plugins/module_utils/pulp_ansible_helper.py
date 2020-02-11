# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import missing_required_lib

from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import (
    PulpEntity,
)
from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_mixins import (
    PulpDistributionMixin,
    PulpRemoteMixin,
    PulpRepositoryMixin,
)

try:
    from pulpcore.client import pulp_ansible
    HAS_PULP_ANSIBLE_CLIENT = True
except ImportError:
    class Dummy():
        def __getattr__(self, attr):
            return object

    pulp_ansible = Dummy()

    HAS_PULP_ANSIBLE_CLIENT = False
    PULP_ANSIBLE_CLIENT_IMPORT_ERROR = traceback.format_exc()


class PulpAnsibleEntity(PulpEntity):
    _api_client_class = pulp_ansible.ApiClient

    def __init__(self, module, *args, **kwargs):
        if not HAS_PULP_ANSIBLE_CLIENT:
            module.fail_json(
                msg=missing_required_lib('pulp_ansible-client'),
                exception=PULP_ANSIBLE_CLIENT_IMPORT_ERROR,
            )
        super(PulpAnsibleEntity, self).__init__(module, *args, **kwargs)


class PulpAnsibleDistribution(PulpDistributionMixin, PulpAnsibleEntity):
    _api_class = pulp_ansible.DistributionsAnsibleApi
    _api_entity_class = pulp_ansible.AnsibleAnsibleDistribution


class PulpAnsibleRemote(PulpRemoteMixin, PulpAnsibleEntity):
    _api_class = pulp_ansible.RemotesAnsibleApi
    _api_entity_class = pulp_ansible.AnsibleAnsibleRemote


class PulpAnsibleRepository(PulpRepositoryMixin, PulpAnsibleEntity):
    _api_class = pulp_ansible.RepositoriesAnsibleApi
    _api_entity_class = pulp_ansible.AnsibleAnsibleRepository
