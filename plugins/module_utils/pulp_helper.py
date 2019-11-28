# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from importlib import import_module

from ansible.module_utils.basic import AnsibleModule


PAGE_LIMIT = 20


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

        self._changed = False

    def exit_json(self, changed=False, **kwargs):
        changed |= self._changed
        super(PulpAnsibleModule, self).exit_json(changed=changed, **kwargs)


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, argument_spec={}, **kwargs):
        self._entity_name = kwargs.pop('entity_name')
        self._entity_plural = kwargs.pop('entity_plural')
        self._entity_plugin = kwargs.pop('entity_plugin')
        self._entity_ctlr = None
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

    @property
    def entity_ctlr(self):
        if not self._entity_ctlr:
            self._entity_ctlr = PulpEntityController(
                self,
                self._entity_name,
                self._entity_plural,
                self._entity_plugin
            )
        return self._entity_ctlr

    def process_entity(self, natural_key, desired_attributes):
        if None not in natural_key.values():
            entity = self.entity_ctlr.find(
                natural_key=natural_key,
            )
            entity = self.ensure_entity_state(
                entity=entity,
                natural_key=natural_key,
                desired_attributes=desired_attributes,
            )
            if entity:
                entity = entity.to_dict()
            self.exit_json(**{self._entity_name: entity})
        else:
            entities = self.entity_ctlr.list()
            self.exit_json(**{self._entity_plural: [entity.to_dict() for entity in entities]})

    def ensure_entity_state(self, entity, natural_key, desired_attributes):
        if self.params['state'] == 'present':
            if entity:
                entity = self.entity_ctlr.update(entity, desired_attributes)
            else:
                entity = self.entity_ctlr.create(natural_key, desired_attributes)
        if self.params['state'] == 'absent' and entity is not None:
            entity = self.entity_ctlr.delete(entity)
        return entity


class PulpEntityController:

    def __init__(self, module, entity_name, entity_plural, entity_plugin):
        self.module = module
        # TODO: Why does dynamic 'import_module' fail without below manual import?
        import ansible.module_utils.pulp_file  # noqa: F401
        self._api_client = getattr(import_module("ansible.module_utils.pulp_%s" % entity_plugin.lower()),
                                   "Pulp%sApiClient" % entity_plugin.lower().capitalize()
                                   )(self.module)
        self._api = getattr(self._api_client, entity_plural + '_api')
        self._api_class = getattr(self._api_client, entity_name + '_class')

    @property
    def api(self):
        return self._api

    @property
    def api_client(self):
        return self._api_client

    def find(self, natural_key):
        search_result = self._api.list(**natural_key)
        if search_result.count == 1:
            return search_result.results[0]
        else:
            return None

    def list(self):
        entities = []
        offset = 0
        search_result = self._api.list(limit=PAGE_LIMIT, offset=offset)
        entities.extend(search_result.results)
        while search_result.next:
            offset += PAGE_LIMIT
            search_result = self._api.list(limit=PAGE_LIMIT, offset=offset)
            entities.extend(search_result.results)
        return entities

    def create(self, natural_key, desired_attributes):
        if not hasattr(self._api, 'create'):
            self.module.fail_json(msg="This entity is not creatable.")
        kwargs = dict()
        kwargs.update(natural_key)
        kwargs.update(desired_attributes)
        entity = self._api_class(**kwargs)
        if not self.module.check_mode:
            response = self._api.create(entity)
            if getattr(response, 'task', None):
                task = self._api_client.wait_for_task(response.task)
                entity = self._api.read(task.created_resources[0])
            else:
                entity = response
        self.module._changed = True
        return entity

    def update(self, entity, desired_attributes):
        changed = False
        # drop 'file' because artifacts as well as content units are immutable anyway
        desired_attributes.pop('file', None)
        for key, value in desired_attributes.items():
            if getattr(entity, key, None) != value:
                setattr(entity, key, value)
                changed = True
        if changed:
            if not hasattr(self._api, 'update'):
                self.module.fail_json(msg="This entity is immutable.")
            if not self.module.check_mode:
                response = self._api.update(entity.pulp_href, entity)
                if getattr(response, 'task', None):
                    self._api_client.wait_for_task(response.task)
                    entity = self._api.read(entity.pulp_href)
                else:
                    entity = response
        if changed:
            self.module._changed = True
        return entity

    def delete(self, entity):
        if not hasattr(self._api, 'delete'):
            self.module.fail_json(msg="This entity is not deletable.")
        if not self.module.check_mode:
            response = self._api.delete(entity.pulp_href)
            if getattr(response, 'task', None):
                self._api_client.wait_for_task(response.task)
        self.module._changed = True
        return None
