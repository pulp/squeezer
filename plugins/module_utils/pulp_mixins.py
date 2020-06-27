# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import (
    PulpTask,
)


class PulpDistributionMixin():
    _name_singular = 'distribution'
    _name_plural = 'distributions'


class PulpPublicationMixin():
    _name_singular = 'publication'
    _name_plural = 'publications'

    def find(self):
        # Hack, because you cannot search for publications
        repository_version_href = self.natural_key['repository_version']
        search_result = self.list()
        for item in search_result:
            if item.repository_version == repository_version_href:
                self.entity = item
                break
        return self.entity


class PulpRemoteMixin():
    _name_singular = 'remote'
    _name_plural = 'remotes'


class PulpRepositoryMixin():
    _name_singular = 'repository'
    _name_plural = 'repositories'

    def sync(self, remote_href):
        response = self.api.sync(self.entity.pulp_href, {'remote': remote_href})
        return PulpTask(self.module, {'pulp_href': response.task}).wait_for()
