# copyright (c) 2022, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib

GLUE_VERSION_SPEC = ">=0.29.2,<0.35"
GLUE_DEB_VERSION_SPEC = ">=0.3.0,<0.4"


def assert_version(spec, version, name):
    if not SpecifierSet(spec, prereleases=True).contains(version):
        raise ImportError(f"Installed '{name}' version '{version}' is not in '{spec}'.")


try:
    from packaging.requirements import SpecifierSet
    from pulp_glue.common import __version__ as pulp_glue_version
    from pulp_glue.common.context import PulpContext, PulpException, PulpNoWait
    from pulp_glue.common.openapi import BasicAuthProvider

    assert_version(GLUE_VERSION_SPEC, pulp_glue_version, "pulp-glue")
    PULP_CLI_IMPORT_ERR = None
except ImportError:
    PULP_CLI_IMPORT_ERR = traceback.format_exc()


class SqueezerException(Exception):
    pass


__VERSION__ = "0.2.1-dev"


class PulpAnsibleModule(AnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = {
            "pulp_url": {"required": True, "fallback": (env_fallback, ["SQUEEZER_PULP_URL"])},
            "username": {"required": False, "fallback": (env_fallback, ["SQUEEZER_USERNAME"])},
            "password": {
                "required": False,
                "no_log": True,
                "fallback": (env_fallback, ["SQUEEZER_PASSWORD"]),
            },
            "user_cert": {"required": False, "no_log": True},
            "user_key": {"required": False, "no_log": True},
            "validate_certs": {
                "type": "bool",
                "default": True,
                "fallback": (env_fallback, ["SQUEEZER_VALIDATE_CERTS"]),
            },
            "refresh_api_cache": {"type": "bool", "default": False},
            "timeout": {"type": "int", "default": 3600},
        }
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

        auth_args = {}
        if self.params["username"]:
            auth_args["auth_provider"] = BasicAuthProvider(
                username=self.params["username"],
                password=self.params["password"],
            )

        self.pulp_ctx = PulpContext(
            api_root="/pulp/",
            api_kwargs=dict(
                base_url=self.params["pulp_url"],
                cert=self.params["user_cert"],
                key=self.params["user_key"],
                validate_certs=self.params["validate_certs"],
                refresh_cache=self.params["refresh_api_cache"],
                user_agent=f"Squeezer/{__VERSION__}",
                **auth_args,
            ),
            background_tasks=False,
            timeout=self.params["timeout"],
            fake_mode=self.check_mode,  # This sets api_kwargs["safe_calls_only"] for us.
        )

    def __enter__(self):
        self._changed = False
        self._results = {}
        self._diff_states = []

        return self

    def __exit__(self, exc_class, exc_value, tb):
        if exc_class is None:
            if self._diff_states:
                self._results["diff"] = {
                    "before": self._diff_states[0],
                    "after": self._diff_states[-1],
                }
            self.exit_json(changed=self._changed, **self._results)
        else:
            if issubclass(exc_class, (PulpException, PulpNoWait, SqueezerException)):
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

    def record_diff_state(self, value):
        self._diff_states.append(value)


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, context_class, entity_singular, entity_plural, **kwargs):
        argument_spec = {
            "state": {
                "choices": ["present", "absent"],
            },
        }
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

    def process(self, natural_key, desired_attributes, defaults=None):
        if self.state is None:
            return self.process_info(natural_key, desired_attributes)

        if "pulp_href" in natural_key:
            self.context.pulp_href = natural_key["pulp_href"]
        else:
            if None in natural_key.values():
                raise SqueezerException("Insufficient information to identify the entity.")
            self.context.entity = natural_key

        if self.state == "present":
            desired_entity = desired_attributes
        elif self.state == "absent":
            desired_entity = None
        else:
            self.set_result(
                self.entity_singular,
                self.process_special(desired_attributes, defaults=defaults),
            )
            return
        changed, before, after = self.process_converge(desired_entity, defaults=defaults)
        if before is not None:
            before = self.represent(before)
        if after is not None:
            after = self.represent(after)
        if changed:
            self.set_changed()
            self.record_diff_state(before)
            self.record_diff_state(after)
        self.set_result(self.entity_singular, after)

    def process_converge(self, desired_entity, defaults=None):
        return self.context.converge(desired_entity, defaults=defaults)

    def process_info(self, natural_key, desired_attributes):
        if any((value is not None for value in desired_attributes.values())):
            raise SqueezerException("Cannot use attributes when querying entities.")
        # TODO turn this into a filtering query instead
        if None in natural_key.values():
            entities = [
                self.represent(entity)
                for entity in self.context.list(limit=-1, offset=0, parameters={})
            ]
            self.set_result(self.entity_plural, entities)
        else:
            if "pulp_href" in natural_key:
                self.context.pulp_href = natural_key["pulp_href"]
            else:
                self.context.entity = natural_key
            self.set_result(self.entity_singular, self.represent(self.context.entity))

    def process_special(self, entity, natural_key, desired_attributes, defaults=None):
        raise SqueezerException(f"Invalid state '{self.state}'.")


class PulpRemoteAnsibleModule(PulpEntityAnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = {
            "name": {},
            "url": {},
            "headers": {
                "type": "list",
                "elements": "dict",
            },
            "remote_username": {"no_log": True},
            "remote_password": {"no_log": True},
            "ca_cert": {},
            "client_cert": {},
            "client_key": {"no_log": True},
            "tls_validation": {"type": "bool"},
            "proxy_url": {},
            "proxy_username": {"no_log": True},
            "proxy_password": {"no_log": True},
            "download_concurrency": {"type": "int"},
            "rate_limit": {"type": "int"},
            "total_timeout": {"type": "float"},
            "connect_timeout": {"type": "float"},
            "sock_connect_timeout": {"type": "float"},
            "sock_read_timeout": {"type": "float"},
            "max_retries": {"type": "int"},
        }
        argument_spec.update(kwargs.pop("argument_spec", {}))

        kwargs.setdefault("entity_singular", "remote")
        kwargs.setdefault("entity_plural", "remotes")

        super().__init__(argument_spec=argument_spec, **kwargs)

    def represent(self, entity):
        result = super().represent(entity)
        result.pop("username", None)
        result.pop("password", None)
        result.pop("client_key", None)
        result.pop("proxy_username", None)
        result.pop("proxy_password", None)
        return result

    def process(self, natural_key, desired_attributes):
        desired_attributes.update(
            {
                key: self.params[key]
                for key in [
                    "url",
                    "headers",
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
                    "max_retries",
                ]
                if self.params[key] is not None
            }
        )
        if self.params["remote_username"] is not None:
            desired_attributes["username"] = self.params["remote_username"]
        if self.params["remote_password"] is not None:
            desired_attributes["password"] = self.params["remote_password"]

        super().process(natural_key, desired_attributes)
