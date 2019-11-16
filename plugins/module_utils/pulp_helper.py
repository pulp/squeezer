# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback
import os
from shutil import rmtree
from tempfile import mkdtemp
from time import sleep

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    from pulpcore.client import pulpcore
    HAS_PULPCORE_CLIENT = True
except ImportError:
    class Dummy():
        def __getattr__(self, attr):
            return object

    pulpcore = Dummy()

    HAS_PULPCORE_CLIENT = False
    PULPCORE_CLIENT_IMPORT_ERROR = traceback.format_exc()


PAGE_LIMIT = 20
CONTENT_CHUNK_SIZE = 512 * 1024  # 1/2 MB


class PulpAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec=None, **kwargs):
        if argument_spec is None:
            argument_spec = {}
        self._changed = False

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

        self.api_config = pulpcore.Configuration()
        self.api_config.host = self.params['pulp_url']
        self.api_config.username = self.params['username']
        self.api_config.password = self.params['password']
        self.api_config.verify_ssl = self.params['validate_certs']
        self.api_config.safe_chars_for_path_param = '/'

    def exit_json(self, changed=False, **kwargs):
        changed |= self._changed
        super(PulpAnsibleModule, self).exit_json(changed=changed, **kwargs)


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, argument_spec=None, **kwargs):
        if argument_spec is None:
            argument_spec = {}
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


class PulpEntity(object):
    def __init__(self, module, natural_key=None, desired_attributes=None):
        self.module = module
        self.api_client = self._api_client_class(self.module.api_config)
        self.api = self._api_class(self.api_client)
        self.entity = None
        self.natural_key = natural_key
        self.desired_attributes = desired_attributes

    def find(self):
        search_result = self.api.list(**self.natural_key)
        if search_result.count == 1:
            self.entity = search_result.results[0]
            return self.entity
        else:
            return None

    def list(self):
        entities = []
        offset = 0
        search_result = self.api.list(limit=PAGE_LIMIT, offset=offset)
        entities.extend(search_result.results)
        while search_result.next:
            offset += PAGE_LIMIT
            search_result = self.api.list(limit=PAGE_LIMIT, offset=offset)
            entities.extend(search_result.results)
        return entities

    def create(self):
        if not hasattr(self.api, 'create'):
            self.module.fail_json(msg="This entity is not creatable.")
        kwargs = dict()
        kwargs.update(self.natural_key)
        kwargs.update(self.desired_attributes)
        entity = self._api_entity_class(**kwargs)
        if not self.module.check_mode:
            response = self.api.create(entity)
            if getattr(response, 'task', None):
                task = PulpTask(self.module).wait_for(response.task)
                entity = self.api.read(task.created_resources[0])
            else:
                entity = response
        self.module._changed = True
        self.entity = entity
        return self.entity

    def update(self):
        changed = False
        desired_attributes = self.desired_attributes.copy()
        # drop 'file' because artifacts as well as content units are immutable anyway
        desired_attributes.pop('file', None)
        for key, value in desired_attributes.items():
            if getattr(self.entity, key, None) != value:
                setattr(self.entity, key, value)
                changed = True
        if changed:
            if not hasattr(self.api, 'update'):
                self.module.fail_json(msg="This entity is immutable.")
            if not self.module.check_mode:
                response = self.api.update(self.entity.pulp_href, self.entity)
                if getattr(response, 'task', None):
                    PulpTask(self.module).wait_for(response.task)
                    entity = self.api.read(self.entity.pulp_href)
                else:
                    entity = response
                self.entity = entity
            self.module._changed = True
        return self.entity

    def delete(self):
        if not hasattr(self.api, 'delete'):
            self.module.fail_json(msg="This entity is not deletable.")
        if not self.module.check_mode:
            response = self.api.delete(self.entity.pulp_href)
            if getattr(response, 'task', None):
                PulpTask(self.module).wait_for(response.task)
        self.module._changed = True
        return None

    def process(self):
        if None not in self.natural_key.values():
            entity = self.find()
            if self.module.params['state'] == 'present':
                if entity is None:
                    entity = self.create()
                else:
                    entity = self.update()
            elif self.module.params['state'] == 'absent' and entity is not None:
                entity = self.delete()

            if entity:
                entity = entity.to_dict()
            self.module.exit_json(**{self._name_singular: entity})
        else:
            entities = self.list()
            self.module.exit_json(**{self._name_plural: [entity.to_dict() for entity in entities]})


class PulpArtifact(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_entity_class = pulpcore.Artifact

    _name_singular = 'artifact'
    _name_plural = 'artifacts'

    def _api_class(self, *args, **kwargs):
        scope = self

        class NewArtifactsApi(pulpcore.ArtifactsApi):
            def create(self, entity, **kwargs):
                size = os.stat(entity.file).st_size
                if size > CONTENT_CHUNK_SIZE:
                    artifact_href = PulpUpload(scope.module).chunked_upload(entity.file, entity.sha256, size)
                    return self.read(artifact_href)
                # TODO Why is the ArtifactsApi strange with create?
                payload = {
                    'file': entity.file,
                    'sha256': entity.sha256,
                }
                payload.update(kwargs)
                return super(NewArtifactsApi, self).create(**payload)

        return NewArtifactsApi(*args, **kwargs)


class PulpStatus(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_class = pulpcore.StatusApi


class PulpTask(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_class = pulpcore.TasksApi
    _api_entity_class = pulpcore.Task

    _name_singular = 'task'
    _name_plural = 'tasks'

    def wait_for(self, task_href):
        task = self.api.read(task_href)
        while task.state not in ['completed', 'failed', 'canceled']:
            sleep(2)
            task = self.api.read(task.pulp_href)
        if task.state != 'completed':
            self.module.fail_json(msg='Task failed to complete. ({1}; {2})'.format(task.state, task.error['description']))
        return task


class PulpUpload(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_class = pulpcore.UploadsApi

    def chunked_upload(self, path, sha256, size):
        offset = 0

        upload = self.api.create(pulpcore.Upload(size=size))
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
                        upload = self.api.update(
                            upload_href=upload.pulp_href,
                            file=chunk_file_name,
                            content_range=content_range,
                        )
                    finally:
                        rmtree(temp_dir)
                    offset += actual_chunk_size

                commit_response = self.api.commit(
                    upload.pulp_href, pulpcore.UploadCommit(sha256=sha256)
                )
                commit_task = PulpTask(self.module).wait_for(commit_response.task)
                artifact_href = commit_task.created_resources[0]
        except Exception:
            self.api.delete(upload.pulp_href)
            raise

        return artifact_href
