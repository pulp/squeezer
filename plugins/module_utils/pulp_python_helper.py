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
    from pulpcore.client import pulp_python
    HAS_PULP_PYTHON_CLIENT = True
except ImportError:
    class Dummy():
        def __getattr__(self, attr):
            return Dummy()

    pulp_python = Dummy()

    HAS_PULP_PYTHON_CLIENT = False
    PULP_PYTHON_CLIENT_IMPORT_ERROR = traceback.format_exc()


ProjectSpecifier = pulp_python.models.project_specifier.ProjectSpecifier


class PulpPythonEntity(PulpEntity):
    _api_client_class = pulp_python.ApiClient

    def __init__(self, module, *args, **kwargs):
        if not HAS_PULP_PYTHON_CLIENT:
            module.fail_json(
                msg=missing_required_lib('pulp_python-client'),
                exception=PULP_PYTHON_CLIENT_IMPORT_ERROR,
            )
        super(PulpPythonEntity, self).__init__(module, *args, **kwargs)


class PulpPythonContent(PulpPythonEntity):
    _name_singular = 'package'
    _name_plural = 'packages'

    def _api_class(self, *args, **kwargs):

        class NewPythonContentsApi(pulp_python.ContentFilesApi):
            def create(self, entity, **kwargs):
                # TODO Why is the FileContentsApi strange with create?
                payload = {
                    'artifact': entity.artifact,
                    'relative_path': entity.relative_path,
                }
                payload.update(kwargs)
                return super(NewPythonContentsApi, self).create(**payload)
        return NewPythonContentsApi(*args, **kwargs)

    def _api_entity_class(self, *args, **kwargs):
        scope = self

        class NewPythonContent(pulp_python.PythonFileContent):
            def __init__(self, **kwargs):
                # FileContent can only be searched by digest,
                # while it wants artifact to create.
                if 'sha256' in kwargs:
                    artifact = PulpArtifact(scope.module, {'sha256': kwargs.pop('sha256')}).find()
                    kwargs['artifact'] = artifact.pulp_href
                super(NewPythonContent, self).__init__(**kwargs)

        return NewPythonContent(*args, **kwargs)


class PulpPythonDistribution(PulpDistributionMixin, PulpPythonEntity):
    _api_class = pulp_python.DistributionsPypiApi
    _api_entity_class = pulp_python.PythonPythonDistribution


class PulpPythonPublication(PulpPublicationMixin, PulpPythonEntity):
    _api_class = pulp_python.PublicationsPypiApi
    _api_entity_class = pulp_python.PythonPythonPublication


class PulpPythonRemote(PulpRemoteMixin, PulpPythonEntity):
    _api_class = pulp_python.RemotesPythonApi
    _api_entity_class = pulp_python.PythonPythonRemote


class PulpPythonRepository(PulpRepositoryMixin, PulpPythonEntity):
    _api_class = pulp_python.RepositoriesPythonApi
    _api_entity_class = pulp_python.PythonPythonRepository
