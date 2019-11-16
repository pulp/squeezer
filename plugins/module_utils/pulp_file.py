# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import missing_required_lib

from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_helper import (
    PulpArtifact,
    PulpEntity,
    PulpTask,
)

try:
    from pulpcore.client import pulp_file
    HAS_PULP_FILE_CLIENT = True
except ImportError:
    class Dummy():
        def __getattr__(self, attr):
            return object

    pulp_file = Dummy()

    HAS_PULP_FILE_CLIENT = False
    PULP_FILE_CLIENT_IMPORT_ERROR = traceback.format_exc()


class PulpFileEntity(PulpEntity):
    _api_client_class = pulp_file.ApiClient

    def __init__(self, module, *args, **kwargs):
        if not HAS_PULP_FILE_CLIENT:
            module.fail_json(
                msg=missing_required_lib('pulp_file-client'),
                exception=PULP_FILE_CLIENT_IMPORT_ERROR,
            )
        super(PulpFileEntity, self).__init__(module, *args, **kwargs)


class PulpFileContent(PulpFileEntity):
    _api_class = pulp_file.ContentFilesApi

    _name_singular = 'content'
    _name_plural = 'contents'

    def _api_class(self, *args, **kwargs):

        class NewFileContentsApi(pulp_file.ContentFilesApi):
            def create(self, entity, **kwargs):
                # TODO Why is the FileContentsApi strange with create?
                payload = {
                    'artifact': entity.artifact,
                    'relative_path': entity.relative_path,
                }
                payload.update(kwargs)
                return super(NewFileContentsApi, self).create(**payload)
        return NewFileContentsApi(*args, **kwargs)

    def _api_entity_class(self, *args, **kwargs):
        scope = self

        class NewFileContent(pulp_file.FileFileContent):
            def __init__(self, **kwargs):
                # FileContent can only be searched by digest,
                # while it wants srtifact to create.
                if 'digest' in kwargs:
                    artifact = PulpArtifact(scope.module, {'sha256': kwargs.pop('digest')}).find()
                    kwargs['artifact'] = artifact.pulp_href
                super(NewFileContent, self).__init__(**kwargs)

        return NewFileContent(*args, **kwargs)


class PulpFileDistribution(PulpFileEntity):
    _api_class = pulp_file.DistributionsFileApi
    _api_entity_class = pulp_file.FileFileDistribution

    _name_singular = 'distribution'
    _name_plural = 'distributions'


class PulpFilePublication(PulpFileEntity):
    _api_class = pulp_file.PublicationsFileApi
    _api_entity_class = pulp_file.FileFilePublication

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


class PulpFileRemote(PulpFileEntity):
    _api_class = pulp_file.RemotesFileApi
    _api_entity_class = pulp_file.FileFileRemote

    _name_singular = 'remote'
    _name_plural = 'remotes'


class PulpFileRepository(PulpFileEntity):
    _api_class = pulp_file.RepositoriesFileApi
    _api_entity_class = pulp_file.FileFileRepository

    _name_singular = 'repository'
    _name_plural = 'repositories'

    def sync(self, remote_href):
        response = self.api.sync(self.entity.pulp_href, {'remote': remote_href})
        return PulpTask(self.module).wait_for(response.task)
