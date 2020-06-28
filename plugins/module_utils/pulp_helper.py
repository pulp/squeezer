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
            return Dummy()

    pulpcore = Dummy()

    HAS_PULPCORE_CLIENT = False
    PULPCORE_CLIENT_IMPORT_ERROR = traceback.format_exc()


PAGE_LIMIT = 20
CONTENT_CHUNK_SIZE = 512 * 1024  # 1/2 MB


class PulpAnsibleModule(AnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = dict(
            pulp_url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            validate_certs=dict(type='bool', default=True),
        )
        argument_spec.update(kwargs.pop('argument_spec', {}))
        supports_check_mode = kwargs.pop('supports_check_mode', True)
        super(PulpAnsibleModule, self).__init__(argument_spec=argument_spec, supports_check_mode=supports_check_mode, **kwargs)

        if not HAS_PULPCORE_CLIENT:
            self.fail_json(
                msg=missing_required_lib("pulpcore-client"),
                exception=PULPCORE_CLIENT_IMPORT_ERROR,
            )

    def __enter__(self):
        self._changed = False
        self._results = {}

        self.api_config = pulpcore.Configuration()
        self.api_config.host = self.params['pulp_url']
        self.api_config.username = self.params['username']
        self.api_config.password = self.params['password']
        self.api_config.verify_ssl = self.params['validate_certs']
        self.api_config.safe_chars_for_path_param = '/'

        return self

    def __exit__(self, exc_class, exc_value, traceback):
        if exc_class is not None:
            if issubclass(exc_class, Exception):
                self.fail_json(msg=str(exc_value), changed=self._changed)
                return True
        self.exit_json(changed=self._changed, **self._results)

    def set_changed(self):
        self._changed = True

    def set_result(self, key, value):
        self._results[key] = value


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = dict(
            state=dict(
                choices=['present', 'absent'],
            ),
        )
        argument_spec.update(kwargs.pop('argument_spec', {}))
        super(PulpEntityAnsibleModule, self).__init__(argument_spec=argument_spec, **kwargs)


class PulpEntity(object):
    def __init__(self, module, natural_key=None, desired_attributes=None):
        self.module = module
        self.api_client = self._api_client_class(self.module.api_config)
        self.api = self._api_class(self.api_client)
        self.entity = None
        self.natural_key = natural_key
        self.desired_attributes = desired_attributes

    def find(self):
        search_result = self.api.list(**self.natural_key, limit=1)
        if search_result.count == 1:
            self.entity = search_result.results[0]
        else:
            self.entity = None
        return self.entity

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
            raise Exception("This entity is not creatable.")
        kwargs = dict()
        kwargs.update(self.natural_key)
        kwargs.update(self.desired_attributes)
        self.entity = self._api_entity_class(**kwargs)
        if not self.module.check_mode:
            response = self.api.create(self.entity)
            if getattr(response, 'task', None):
                task = PulpTask(self.module, {'pulp_href': response.task}).wait_for()
                self.entity = self.api.read(task.created_resources[0])
            else:
                self.entity = response
        self.module.set_changed()
        return self.entity

    def update(self):
        changed = False
        for key, value in self.desired_attributes.items():
            # Skip 'file' because artifacts as well as content units are immutable anyway
            if key == 'file':
                continue
            if getattr(self.entity, key, None) != value:
                setattr(self.entity, key, value)
                changed = True
        if changed:
            if not hasattr(self.api, 'update'):
                raise Exception("This entity is immutable.")
            if not self.module.check_mode:
                response = self.api.update(self.entity.pulp_href, self.entity)
                if getattr(response, 'task', None):
                    PulpTask(self.module, {'pulp_href': response.task}).wait_for()
                    self.entity = self.api.read(self.entity.pulp_href)
                else:
                    self.entity = response
            self.module.set_changed()
        return self.entity

    def delete(self):
        if not hasattr(self.api, 'delete'):
            raise Exception("This entity is not deletable.")
        if not self.module.check_mode:
            response = self.api.delete(self.entity.pulp_href)
            if getattr(response, 'task', None):
                PulpTask(self.module, {'pulp_href': response.task}).wait_for()
        self.entity = None
        self.module.set_changed()
        return self.entity

    def process_special(self):
        raise Exception("Invalid state ({0}) for entity.".format(self.module.params['state']))

    def process(self):
        if None not in self.natural_key.values():
            self.find()
            if self.module.params['state'] is None:
                pass
            elif self.module.params['state'] == 'present':
                if self.entity is None:
                    self.create()
                else:
                    self.update()
            elif self.module.params['state'] == 'absent':
                if self.entity is not None:
                    self.delete()
            else:
                self.process_special()

            entity_dict = self.entity.to_dict() if self.entity else None
            self.module.set_result(self._name_singular, entity_dict)
        else:
            entities = self.list()
            self.module.set_result(self._name_plural, [entity.to_dict() for entity in entities])


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


class PulpOrphans(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_class = pulpcore.OrphansApi

    def delete(self):
        if not self.module.check_mode:
            response = self.api.delete()
            task = PulpTask(self.module, {'pulp_href': response.task}).wait_for().to_dict()
            response = task["progress_reports"]
            response = {item["message"].split(" ")[-1].lower(): item["total"] for item in response}
        else:
            response = {
                "artifacts": 0,
                "content": 0,
            }
        self.module.set_changed()
        return response


class PulpStatus(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_class = pulpcore.StatusApi


class PulpTask(PulpEntity):
    _api_client_class = pulpcore.ApiClient
    _api_class = pulpcore.TasksApi
    _api_entity_class = pulpcore.Task

    _name_singular = 'task'
    _name_plural = 'tasks'

    def find(self):
        self.entity = self.api.read(self.natural_key["pulp_href"])
        return self.entity

    def process_special(self):
        if self.module.params['state'] in ['canceled', 'completed']:
            if self.entity is None:
                raise Exception("Entity not found.")
            if self.entity.state in ['waiting', 'running']:
                self.module.set_changed()
                self.entity.state = self.module.params['state']
                if not self.module.check_mode:
                    if self.module.params['state'] == 'canceled':
                        self.api.tasks_cancel(self.entity.pulp_href, self.entity)
                    self.wait_for(desired_state=self.module.params['state'])
        else:
            super(PulpTask, self).process_special()

    def wait_for(self, desired_state='completed'):
        self.find()
        while self.entity.state not in ['completed', 'failed', 'canceled']:
            sleep(2)
            self.find()
        if self.entity.state != desired_state:
            if self.entity.state == 'failed':
                raise Exception('Task failed to complete. ({0}; {1})'.format(self.entity.state, self.entity.error['description']))
            raise Exception('Task did not reach {0} state'.format(desired_state))
        return self.entity


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

                response = self.api.commit(
                    upload.pulp_href, pulpcore.UploadCommit(sha256=sha256)
                )
                task = PulpTask(self.module, {'pulp_href': response.task}).wait_for()
                artifact_href = task.created_resources[0]
        except Exception:
            self.api.delete(upload.pulp_href)
            raise

        return artifact_href
