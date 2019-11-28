# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
from shutil import rmtree
from tempfile import mkdtemp
from time import sleep
import traceback

from ansible.module_utils.basic import missing_required_lib

try:
    from pulpcore.client import pulpcore
    HAS_PULPCORE_CLIENT = True
except ImportError:
    pulpcore = None
    HAS_PULPCORE_CLIENT = False
    PULPCORE_CLIENT_IMPORT_ERROR = traceback.format_exc()


CONTENT_CHUNK_SIZE = 512 * 1024  # 1/2 MB


class PulpCoreApiClient():

    def __init__(self, module):
        self.module = module

        if not HAS_PULPCORE_CLIENT:
            self.module.fail_json(
                msg=missing_required_lib("pulpcore-client"),
                exception=PULPCORE_CLIENT_IMPORT_ERROR,
            )

        self._api_config = pulpcore.Configuration()
        self._api_config.host = self.module.params['pulp_url']
        self._api_config.username = self.module.params['username']
        self._api_config.password = self.module.params['password']
        self._api_config.verify_ssl = self.module.params['validate_certs']
        self._api_config.safe_chars_for_path_param = '/'

        self._client = None
        self._plugin_client = None

        self._artifacts_api = None
        self._status_api = None
        self._tasks_api = None
        self._uploads_api = None

    @property
    def client(self):
        if not self._client:
            self._client = pulpcore.ApiClient(self._api_config)
        return self._client

    @property
    def artifacts_api(self):
        if not self._artifacts_api:
            api_client = self

            class NewArtifactsApi(pulpcore.ArtifactsApi):
                def create(self, entity, **kwargs):
                    size = os.stat(entity.file).st_size
                    if size > CONTENT_CHUNK_SIZE:
                        return api_client.chunked_upload(entity.file, entity.sha256, size)
                    # TODO Why is the ArtifactsApi strange with create?
                    payload = {
                        'file': entity.file,
                        'sha256': entity.sha256,
                    }
                    payload.update(kwargs)
                    return super(NewArtifactsApi, self).create(**payload)

            self._artifacts_api = NewArtifactsApi(self.client)
        return self._artifacts_api

    @property
    def artifact_class(self):
        return pulpcore.Artifact

    @property
    def status_api(self):
        if not self._status_api:
            self._status_api = pulpcore.StatusApi(self.client)
        return self._status_api

    @property
    def status_class(self):
        return pulpcore.Status

    @property
    def tasks_api(self):
        if not self._tasks_api:
            self._tasks_api = pulpcore.TasksApi(self.client)
        return self._tasks_api

    @property
    def uploads_api(self):
        if not self._uploads_api:
            self._uploads_api = pulpcore.UploadsApi(self.client)
        return self._uploads_api

    def chunked_upload(self, path, sha256, size):
        offset = 0

        upload = self.uploads_api.create(pulpcore.Upload(size=size))
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(CONTENT_CHUNK_SIZE), b""):
                    actual_chunk_size = len(chunk)
                    content_range = 'bytes {start}-{end}/{size}'.format(
                        start=offset,
                        end=offset + actual_chunk_size - 1,
                        size=size,
                    )
                    temp_dir = mkdtemp(dir="/tmp")
                    try:
                        chunk_file_name = os.path.join(temp_dir, 'chunk.bin')
                        with open(chunk_file_name, 'wb') as chunk_file:
                            chunk_file.write(chunk)
                        upload = self.uploads_api.update(
                            upload_href=upload.pulp_href,
                            file=chunk_file_name,
                            content_range=content_range,
                        )
                    finally:
                        rmtree(temp_dir)
                    offset += actual_chunk_size

                commit_response = self.uploads_api.commit(
                    upload.pulp_href, pulpcore.UploadCommit(sha256=sha256)
                )
                commit_task = self.wait_for_task(commit_response.task)
                artifact = self.artifacts_api.read(commit_task.created_resources[0])
        except Exception:
            self.uploads_api.delete(upload.pulp_href)
            raise

        return artifact

    def wait_for_task(self, task_href):
        task = self.tasks_api.read(task_href)
        while task.state not in ['completed', 'failed', 'canceled']:
            sleep(2)
            task = self.tasks_api.read(task.pulp_href)
        if task.state != 'completed':
            self.module.fail_json(msg='Task failed to complete. ({}; {})'.format(task.state, task.error['description']))
        return task
