# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import traceback
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


class PulpAnsibleModule(AnsibleModule):

    PAGE_LIMIT = 20

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
        self._file_distributions_api = None
        self._file_publications_api = None
        self._file_remotes_api = None
        self._repositories_api = None
        self._status_api = None
        self._tasks_api = None

        self._changed = False

    @property
    def artifacts_api(self):
        if not self._artifacts_api:
            self._artifacts_api = pulpcore.ArtifactsApi(self._client)
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
    def file_distributions_api(self):
        if not self._file_distributions_api:
            client = self.file_client
            self._file_distributions_api = pulp_file.DistributionsFileApi(client)
        return self._file_distributions_api

    @property
    def file_distribution_class(self):
        return pulp_file.FileDistribution

    @property
    def file_publications_api(self):
        if not self._file_publications_api:
            client = self.file_client
            self._file_publications_api = pulp_file.PublicationsFileApi(client)
        return self._file_publications_api

    @property
    def file_publication_class(self):
        return pulp_file.FilePublication

    @property
    def file_remotes_api(self):
        if not self._file_remotes_api:
            client = self.file_client
            self._file_remotes_api = pulp_file.RemotesFileApi(client)
        return self._file_remotes_api

    @property
    def file_remote_class(self):
        return pulp_file.FileRemote

    @property
    def repositories_api(self):
        if not self._repositories_api:
            self._repositories_api = pulpcore.RepositoriesApi(self._client)
        return self._repositories_api

    @property
    def repository_class(self):
        return pulpcore.Repository

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

    def list_entities(self, entity_api):
        entities = []
        offset = 0
        search_result = entity_api.list(limit=self.PAGE_LIMIT, offset=offset)
        entities.extend(search_result.results)
        while search_result.next:
            offset += self.PAGE_LIMIT
            search_result = entity_api.list(limit=self.PAGE_LIMIT, offset=offset)
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
        entity = entity_class(**natural_key, **desired_attributes)
        if not self.check_mode:
            # TODO Why is the ArtifactsApi strange with create?
            if entity_api.__class__.__name__ == 'ArtifactsApi':
                response = entity_api.create(**natural_key, **desired_attributes)
            else:
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
            **kwargs,
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
