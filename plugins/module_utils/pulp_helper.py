# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
from shutil import rmtree
import traceback
from tempfile import mkdtemp
from time import sleep

from ansible.module_utils.basic import (
    AnsibleModule,
    missing_required_lib,
)

try:
    from pulpcore.client import pulpcore
    HAS_PULPCORE_CLIENT = True
except ImportError:
    pulpcore = None
    HAS_PULPCORE_CLIENT = False
    PULPCORE_CLIENT_IMPORT_ERROR = traceback.format_exc()


try:
    from pulpcore.client import pulp_file
    HAS_PULP_FILE_CLIENT = True
except ImportError:
    pulp_file = None
    HAS_PULP_FILE_CLIENT = False
    PULP_FILE_CLIENT_IMPORT_ERROR = traceback.format_exc()


PAGE_LIMIT = 20
CONTENT_CHUNK_SIZE = 512 * 1024  # 1/2 MB


class PulpAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec={}, **kwargs):
        spec = dict(
            pulp_url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            validate_certs=dict(type='bool', default=True),
        )
        spec.update(argument_spec)
        kwargs['supports_check_mode'] = kwargs.get('supports_check_mode', True)
        super(PulpAnsibleModule, self).__init__(argument_spec=spec, **kwargs)
        if not HAS_PULPCORE_CLIENT:
            self.fail_json(
                msg=missing_required_lib("pulpcore-client"),
                exception=PULPCORE_CLIENT_IMPORT_ERROR,
            )
        self._api_config = pulpcore.Configuration()
        self._api_config.host = self.params['pulp_url']
        self._api_config.username = self.params['username']
        self._api_config.password = self.params['password']
        self._api_config.verify_ssl = self.params['validate_certs']
        self._api_config.safe_chars_for_path_param = '/'
        self._client = pulpcore.ApiClient(self._api_config)
        self._file_client = None
        self._artifacts_api = None
        self._file_contents_api = None
        self._file_distributions_api = None
        self._file_publications_api = None
        self._file_remotes_api = None
        self._file_repositories_api = None
        self._status_api = None
        self._tasks_api = None
        self._uploads_api = None

        self._changed = False

    @property
    def artifacts_api(self):
        if not self._artifacts_api:
            module = self

            class NewArtifactsApi(pulpcore.ArtifactsApi):
                def create(self, entity, **kwargs):
                    size = os.stat(entity.file).st_size
                    if size > CONTENT_CHUNK_SIZE:
                        return module.chunked_upload(entity.file, entity.sha256, size)
                    # TODO Why is the ArtifactsApi strange with create?
                    payload = {
                        'file': entity.file,
                        'sha256': entity.sha256,
                    }
                    payload.update(kwargs)
                    return super(NewArtifactsApi, self).create(**payload)

            self._artifacts_api = NewArtifactsApi(self._client)
        return self._artifacts_api

    @property
    def artifact_class(self):
        return pulpcore.Artifact

    @property
    def file_client(self):
        if not self._file_client:
            if not HAS_PULP_FILE_CLIENT:
                self.fail_json(
                    msg=missing_required_lib("pulp_file-client"),
                    exception=PULP_FILE_CLIENT_IMPORT_ERROR,
                )
            self._file_client = pulp_file.ApiClient(self._api_config)
        return self._file_client

    @property
    def file_contents_api(self):
        if not self._file_contents_api:

            class NewFileContentsApi(pulp_file.ContentFilesApi):
                def create(self, entity, **kwargs):
                    # TODO Why is the FileContentsApi strange with create?
                    payload = {
                        'artifact': entity.artifact,
                        'relative_path': entity.relative_path,
                    }
                    payload.update(kwargs)
                    return super(NewFileContentsApi, self).create(**payload)

            self._file_contents_api = NewFileContentsApi(self.file_client)
        return self._file_contents_api

    @property
    def file_content_class(self):
        module = self

        class NewFileContent(pulp_file.FileFileContent):
            def __init__(self, **kwargs):
                # FileContent can only be searched by digest, while it wants srtifact to create.
                if 'digest' in kwargs:
                    artifact = module.find_entity(module.artifacts_api, {'sha256': kwargs.pop('digest')})
                    kwargs['artifact'] = artifact.pulp_href
                super(NewFileContent, self).__init__(**kwargs)

        return NewFileContent

    @property
    def file_distributions_api(self):
        if not self._file_distributions_api:
            client = self.file_client
            self._file_distributions_api = pulp_file.DistributionsFileApi(client)
        return self._file_distributions_api

    @property
    def file_distribution_class(self):
        return pulp_file.FileFileDistribution

    @property
    def file_publications_api(self):
        if not self._file_publications_api:
            client = self.file_client
            self._file_publications_api = pulp_file.PublicationsFileApi(client)
        return self._file_publications_api

    @property
    def file_publication_class(self):
        return pulp_file.FileFilePublication

    @property
    def file_remotes_api(self):
        if not self._file_remotes_api:
            client = self.file_client
            self._file_remotes_api = pulp_file.RemotesFileApi(client)
        return self._file_remotes_api

    @property
    def file_remote_class(self):
        return pulp_file.FileFileRemote

    @property
    def file_repositories_api(self):
        if not self._file_repositories_api:
            client = self.file_client
            self._file_repositories_api = pulp_file.RepositoriesFileApi(client)
        return self._file_repositories_api

    @property
    def file_repository_class(self):
        return pulp_file.FileFileRepository

    @property
    def status_api(self):
        if not self._status_api:
            self._status_api = pulpcore.StatusApi(self._client)
        return self._status_api

    @property
    def tasks_api(self):
        if not self._tasks_api:
            self._tasks_api = pulpcore.TasksApi(self._client)
        return self._tasks_api

    @property
    def uploads_api(self):
        if not self._uploads_api:
            self._uploads_api = pulpcore.UploadsApi(self._client)
        return self._uploads_api

    def exit_json(self, changed=False, **kwargs):
        changed |= self._changed
        super(PulpAnsibleModule, self).exit_json(changed=changed, **kwargs)

    def wait_for_task(self, task_href):
        task = self.tasks_api.read(task_href)
        while task.state not in ['completed', 'failed', 'canceled']:
            sleep(2)
            task = self.tasks_api.read(task.pulp_href)
        if task.state != 'completed':
            self.fail_json(msg='Task failed to complete. ({}; {})'.format(task.state, task.error['description']))
        return task

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
                    chunk_file_name = os.path.join(temp_dir, 'chunk.bin')
                    with open(chunk_file_name, 'wb') as chunk_file:
                        chunk_file.write(chunk)
                    upload = self.uploads_api.update(
                        upload_href=upload.pulp_href,
                        file=chunk_file_name,
                        content_range=content_range,
                    )
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

    def list_entities(self, entity_api):
        entities = []
        offset = 0
        search_result = entity_api.list(limit=PAGE_LIMIT, offset=offset)
        entities.extend(search_result.results)
        while search_result.next:
            offset += PAGE_LIMIT
            search_result = entity_api.list(limit=PAGE_LIMIT, offset=offset)
            entities.extend(search_result.results)
        return entities

    def find_entity(self, entity_api, natural_key):
        search_result = entity_api.list(**natural_key)
        if search_result.count == 1:
            return search_result.results[0]
        else:
            return None

    def create_entity(self, entity_api, entity_class, natural_key, desired_attributes):
        if not hasattr(entity_api, 'create'):
            self.fail_json(msg="This entity is not creatable.")
        kwargs = dict()
        kwargs.update(natural_key)
        kwargs.update(desired_attributes)
        entity = entity_class(**kwargs)
        if not self.check_mode:
            response = entity_api.create(entity)
            if getattr(response, 'task', None):
                task = self.wait_for_task(response.task)
                entity = entity_api.read(task.created_resources[0])
            else:
                entity = response
        self._changed = True
        return entity

    def update_entity(self, entity_api, entity, desired_attributes):
        changed = False
        # drop 'file' because artifacts as well as content units are immutable anyway
        desired_attributes.pop('file', None)
        for key, value in desired_attributes.items():
            if getattr(entity, key, None) != value:
                setattr(entity, key, value)
                changed = True
        if changed:
            if not hasattr(entity_api, 'update'):
                self.fail_json(msg="This entity is immutable.")
            if not self.check_mode:
                response = entity_api.update(entity.pulp_href, entity)
                if getattr(response, 'task', None):
                    self.wait_for_task(response.task)
                    entity = entity_api.read(entity.pulp_href)
                else:
                    entity = response
        if changed:
            self._changed = True
        return entity

    def delete_entity(self, entity_api, entity):
        if not hasattr(entity_api, 'delete'):
            self.fail_json(msg="This entity is not deletable.")
        if not self.check_mode:
            response = entity_api.delete(entity.pulp_href)
            if getattr(response, 'task', None):
                self.wait_for_task(response.task)
        self._changed = True
        return None

    def ensure_entity_state(self, entity_api, entity_class, entity, natural_key, desired_attributes):
        if self.params['state'] == 'present':
            if entity:
                entity = self.update_entity(entity_api, entity, desired_attributes)
            else:
                entity = self.create_entity(entity_api, entity_class, natural_key, desired_attributes)
        if self.params['state'] == 'absent' and entity is not None:
            entity = self.delete_entity(entity_api, entity)
        return entity


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, argument_spec={}, **kwargs):
        self._entity_name = kwargs.pop('entity_name')
        self._entity_plural = kwargs.pop('entity_plural')
        spec = dict(
            state=dict(
                choices=['present', 'absent'],
            ),
        )
        spec.update(argument_spec)
        super(PulpEntityAnsibleModule, self).__init__(
            argument_spec=spec,
            **kwargs
        )
        self._entity_api = getattr(self, self._entity_plural + '_api')
        self._entity_class = getattr(self, self._entity_name + '_class')

    def process_entity(self, natural_key, desired_attributes):
        if None not in natural_key.values():
            entity = self.find_entity(
                entity_api=self._entity_api,
                natural_key=natural_key,
            )
            entity = self.ensure_entity_state(
                entity_api=self._entity_api,
                entity_class=self._entity_class,
                entity=entity,
                natural_key=natural_key,
                desired_attributes=desired_attributes,
            )
            if entity:
                entity = entity.to_dict()
            self.exit_json(**{self._entity_name: entity})
        else:
            entities = self.list_entities(self._entity_api)
            self.exit_json(**{self._entity_plural: [entity.to_dict() for entity in entities]})
