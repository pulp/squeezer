# copyright (c) 2022, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib

try:
    from packaging.requirements import SpecifierSet
    from pulp_glue.common import __version__ as pulp_glue_version
    from pulp_glue.common.context import PulpContext, PulpException

    GLUE_VERSION_SPEC = ">=0.20.0,<0.22.0"
    if not SpecifierSet(GLUE_VERSION_SPEC).contains(pulp_glue_version):
        raise ImportError(
            f"Installed 'pulp-glue' version '{pulp_glue_version}' is not in '{GLUE_VERSION_SPEC}'."
        )

    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()
else:

    class PulpSqueezerContext(PulpContext):
        def prompt(self, *args, **kwargs):
            pass

        def echo(self, *args, **kwargs):
            pass


class SqueezerException(Exception):
    pass


__VERSION__ = "0.0.15-dev"


class PulpAnsibleModule(AnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = dict(
            pulp_url=dict(required=True, fallback=(env_fallback, ["SQUEEZER_PULP_URL"])),
            username=dict(required=False, fallback=(env_fallback, ["SQUEEZER_USERNAME"])),
            password=dict(
                required=False,
                no_log=True,
                fallback=(env_fallback, ["SQUEEZER_PASSWORD"]),
            ),
            user_cert=dict(required=False, no_log=True),
            user_key=dict(required=False, no_log=True),
            validate_certs=dict(
                type="bool",
                default=True,
                fallback=(env_fallback, ["SQUEEZER_VALIDATE_CERTS"]),
            ),
            refresh_api_cache=dict(type="bool", default=False),
        )
        argument_spec.update(kwargs.pop("argument_spec", {}))
        if not kwargs.pop("no_auth", False):
            required_one_of = [
                ("username", "user_cert"),
                ("username", "user_key"),
                ("password", "user_cert"),
                ("password", "user_key"),
            ]
            required_one_of.extend(kwargs.pop("required_one_of", []))
            kwargs["required_one_of"] = required_one_of
        kwargs.setdefault("supports_check_mode", True)

        import_errors = [("pulp-glue", PULP_CLI_IMPORT_ERR)]
        import_errors.extend(kwargs.pop("import_errors", []))

        super().__init__(
            argument_spec=argument_spec,
            **kwargs,
        )

        for import_error in import_errors:
            if import_error[1] is not None:
                self.fail_json(msg=missing_required_lib(import_error[0]), exception=import_error[1])

        self.pulp_ctx = PulpSqueezerContext(
            api_root="/pulp/",
            api_kwargs=dict(
                base_url=self.params["pulp_url"],
                username=self.params["username"],
                password=self.params["password"],
                cert=self.params["user_cert"],
                key=self.params["user_key"],
                validate_certs=self.params["validate_certs"],
                refresh_cache=self.params["refresh_api_cache"],
                safe_calls_only=self.check_mode,
                user_agent=f"Squeezer/{__VERSION__}",
            ),
            background_tasks=False,
            timeout=10,
        )

    def __enter__(self):
        self._changed = False
        self._results = {}

        return self

    def __exit__(self, exc_class, exc_value, tb):
        if exc_class is None:
            self.exit_json(changed=self._changed, **self._results)
        else:
            if issubclass(exc_class, (PulpException, SqueezerException)):
                self.fail_json(msg=str(exc_value), changed=self._changed)
                return True
            elif issubclass(exc_class, Exception):
                self.fail_json(
                    msg=str(exc_value),
                    changed=self._changed,
                    exception="\n".join(traceback.format_exception(exc_class, exc_value, tb)),
                )
                return True

    def set_changed(self):
        self._changed = True

    def set_result(self, key, value):
        self._results[key] = value


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, context_class, entity_singular, entity_plural, **kwargs):
        argument_spec = dict(
            state=dict(
                choices=["present", "absent"],
            ),
        )
        argument_spec.update(kwargs.pop("argument_spec", {}))
        super().__init__(argument_spec=argument_spec, **kwargs)
        self.state = self.params["state"]
        self.context = context_class(self.pulp_ctx)
        self.entity_singular = entity_singular
        self.entity_plural = entity_plural

    def represent(self, entity):
        return {
            key: "" if (key in self.context.NULLABLES and value is None) else value
            for key, value in entity.items()
        }

    def process(self, natural_key, desired_attributes):
        if None not in natural_key.values():
            if "pulp_href" in natural_key:
                self.context.pulp_href = natural_key["pulp_href"]
            else:
                self.context.entity = natural_key
            try:
                entity = self.represent(self.context.entity)
            except PulpException:
                entity = None
            if self.state is None:
                pass
            elif self.state == "absent":
                if entity is not None:
                    if not self.check_mode:
                        self.context.delete()
                    entity = None
                    self.set_changed()
            elif self.state == "present":
                entity = self.process_present(entity, natural_key, desired_attributes)
            else:
                entity = self.process_special(entity, natural_key, desired_attributes)
            self.set_result(self.entity_singular, entity)
        else:
            if self.state is not None:
                raise SqueezerException(f"Invalid state '{self.state}' for entity listing.")
            entities = [
                self.represent(entity)
                for entity in self.context.list(limit=-1, offset=0, parameters={})
            ]
            self.set_result(self.entity_plural, entities)

    def process_present(self, entity, natural_key, desired_attributes):
        if entity is None:
            entity = {**desired_attributes, **natural_key}
            if not self.check_mode:
                self.context.create(body=entity)
                entity = self.context.entity
            entity = self.represent(entity)
            self.set_changed()
        else:
            updated_attributes = {k: v for k, v in desired_attributes.items() if entity[k] != v}
            if updated_attributes:
                if not self.check_mode:
                    self.context.update(body=updated_attributes)
                    entity = self.context.entity
                else:
                    entity.update(updated_attributes)
                entity = self.represent(entity)
                self.set_changed()
        return entity

    def process_special(self, entity, natural_key, desired_attributes):
        raise SqueezerException(f"Invalid state '{self.state}'.")


class PulpRemoteAnsibleModule(PulpEntityAnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = dict(
            name=dict(),
            url=dict(),
            remote_username=dict(no_log=True),
            remote_password=dict(no_log=True),
            ca_cert=dict(),
            client_cert=dict(),
            client_key=dict(no_log=True),
            tls_validation=dict(type="bool"),
            proxy_url=dict(),
            proxy_username=dict(no_log=True),
            proxy_password=dict(no_log=True),
            download_concurrency=dict(type="int"),
            rate_limit=dict(type="int"),
            total_timeout=dict(type="float"),
            connect_timeout=dict(type="float"),
            sock_connect_timeout=dict(type="float"),
            sock_read_timeout=dict(type="float"),
            max_retires=dict(type="int"),
        )
        argument_spec.update(kwargs.pop("argument_spec", {}))

        kwargs.setdefault("entity_singular", "remote")
        kwargs.setdefault("entity_plural", "remotes")

        super().__init__(argument_spec=argument_spec, **kwargs)

    def process(self, natural_key, desired_attributes):
        desired_attributes.update(
            {
                key: self.params[key]
                for key in [
                    "url",
                    "policy",
                    "tls_validation",
                    "proxy_url",
                    "proxy_username",
                    "proxy_password",
                    "ca_cert",
                    "client_cert",
                    "client_key",
                    "download_concurrency",
                    "rate_limit",
                    "total_timeout",
                    "connect_timeout",
                    "sock_connect_timeout",
                    "sock_read_timeout",
                    "max_retires",
                ]
                if self.params[key] is not None
            }
        )
        if self.params["remote_username"] is not None:
            desired_attributes["username"] = self.params["remote_username"]
        if self.params["remote_password"] is not None:
            desired_attributes["password"] = self.params["remote_password"]

        super().process(natural_key, desired_attributes)
