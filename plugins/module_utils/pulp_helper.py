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
        self._file_distributions_api = None
        self._file_publications_api = None
        self._file_remotes_api = None
        self._repositories_api = None
        self._status_api = None
        self._tasks_api = None

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
    def file_publications_api(self):
        if not self._file_publications_api:
            client = self.file_client
            self._file_publications_api = pulp_file.PublicationsFileApi(client)
        return self._file_publications_api

    @property
    def file_remotes_api(self):
        if not self._file_remotes_api:
            client = self.file_client
            self._file_remotes_api = pulp_file.RemotesFileApi(client)
        return self._file_remotes_api

    @property
    def repositories_api(self):
        if not self._repositories_api:
            self._repositories_api = pulpcore.RepositoriesApi(self._client)
        return self._repositories_api

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

    def wait_for_task(self, task_href):
        task = self.tasks_api.read(task_href)
        while task.state not in ['completed', 'failed', 'canceled']:
            sleep(2)
            task = self.tasks_api.read(task.href)
        if task.state != 'completed':
            self.fail_json(msg='Task failed to complete. ({}; {})'.format(task.state, task.error['description']))
        return task

    def list_all(self, api):
        entities = []
        offset = 0
        search_result = api.list(limit=self.PAGE_LIMIT, offset=offset)
        entities.extend(search_result.results)
        while search_result.next:
            offset += module.PAGE_LIMIT
            search_result = api.list(limit=self.PAGE_LIMIT, offset=offset)
            entities.extend(search_result.results)
        return entities
