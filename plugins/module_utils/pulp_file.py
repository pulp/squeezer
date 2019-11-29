# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.pulp_core import PulpCoreApiClient
from ansible.module_utils.pulp_helper import PulpEntityController

try:
    from pulpcore.client import pulp_file
    HAS_PULP_FILE_CLIENT = True
except ImportError:
    pulp_file = None
    HAS_PULP_FILE_CLIENT = False
    PULP_FILE_CLIENT_IMPORT_ERROR = traceback.format_exc()


class PulpFileApiClient(PulpCoreApiClient):

    def __init__(self, module):
        PulpCoreApiClient.__init__(self, module)

        self._contents_api = None
        self._distributions_api = None
        self._publications_api = None
        self._remotes_api = None
        self._repositories_api = None

    @property
    def plugin_client(self):
        if not self._plugin_client:
            if not HAS_PULP_FILE_CLIENT:
                self.fail_json(
                    msg=missing_required_lib("pulp_file-client"),
                    exception=PULP_FILE_CLIENT_IMPORT_ERROR,
                )
            self._plugin_client = pulp_file.ApiClient(self._api_config)
        return self._plugin_client

    @property
    def contents_api(self):
        if not self._contents_api:

            class NewFileContentsApi(pulp_file.ContentFilesApi):
                def create(self, entity, **kwargs):
                    # TODO Why is the FileContentsApi strange with create?
                    payload = {
                        'artifact': entity.artifact,
                        'relative_path': entity.relative_path,
                    }
                    payload.update(kwargs)
                    return super(NewFileContentsApi, self).create(**payload)

            self._contents_api = NewFileContentsApi(self.plugin_client)
        return self._contents_api

    @property
    def content_class(self):
        module = self.module

        class NewFileContent(pulp_file.FileFileContent):
            def __init__(self, **kwargs):
                # FileContent can only be searched by digest, while it wants artifact to create.
                if 'digest' in kwargs:
                    entity_ctlr = PulpEntityController(module, 'artifact', 'artifacts', 'file')
                    artifact = entity_ctlr.find({'sha256': kwargs.pop('digest')})
                    kwargs['artifact'] = artifact.pulp_href
                super(NewFileContent, self).__init__(**kwargs)

        return NewFileContent

    @property
    def distributions_api(self):
        if not self._distributions_api:
            self._distributions_api = pulp_file.DistributionsFileApi(self.plugin_client)
        return self._distributions_api

    @property
    def distribution_class(self):
        return pulp_file.FileFileDistribution

    @property
    def publications_api(self):
        if not self._publications_api:
            self._publications_api = pulp_file.PublicationsFileApi(self.plugin_client)
        return self._publications_api

    @property
    def publication_class(self):
        return pulp_file.FileFilePublication

    @property
    def repositories_api(self):
        if not self._repositories_api:
            self._repositories_api = pulp_file.RepositoriesFileApi(self.plugin_client)
        return self._repositories_api

    @property
    def repository_class(self):
        return pulp_file.FileFileRepository

    @property
    def remotes_api(self):
        if not self._remotes_api:
            self._remotes_api = pulp_file.RemotesFileApi(self.plugin_client)
        return self._remotes_api

    @property
    def remote_class(self):
        return pulp_file.FileFileRemote
