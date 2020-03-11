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
)
from ansible_collections.mdellweg.squeezer.plugins.module_utils.pulp_mixins import (
    PulpDistributionMixin,
    PulpPublicationMixin,
    PulpRemoteMixin,
    PulpRepositoryMixin,
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
                # while it wants artifact to create.
                if 'sha256' in kwargs:
                    artifact = PulpArtifact(scope.module, {'sha256': kwargs.pop('sha256')}).find()
                    kwargs['artifact'] = artifact.pulp_href
                super(NewFileContent, self).__init__(**kwargs)

        return NewFileContent(*args, **kwargs)


class PulpFileDistribution(PulpDistributionMixin, PulpFileEntity):
    _api_class = pulp_file.DistributionsFileApi
    _api_entity_class = pulp_file.FileFileDistribution


class PulpFilePublication(PulpPublicationMixin, PulpFileEntity):
    _api_class = pulp_file.PublicationsFileApi
    _api_entity_class = pulp_file.FileFilePublication


class PulpFileRemote(PulpRemoteMixin, PulpFileEntity):
    _api_class = pulp_file.RemotesFileApi
    _api_entity_class = pulp_file.FileFileRemote


class PulpFileRepository(PulpRepositoryMixin, PulpFileEntity):
    _api_class = pulp_file.RepositoriesFileApi
    _api_entity_class = pulp_file.FileFileRepository
