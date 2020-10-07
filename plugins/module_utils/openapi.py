# -*- coding: utf-8 -*-

# copyright (c) 2020, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import errno
import json
import os
import uuid
from ansible.module_utils import six
from ansible.module_utils.urls import Request
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six.moves.urllib.parse import urlencode, urljoin


if six.PY2:

    def makedirs(path, exist_ok=False):
        try:
            os.makedirs(path)
        except OSError as exc:
            # emulate 'mkdir -p'
            if not (exist_ok and exc.errno == errno.EEXIST and os.path.isdir(path)):
                raise


else:
    makedirs = os.makedirs


class OpenAPI:
    def __init__(
        self,
        base_url,
        doc_path,
        username=None,
        password=None,
        validate_certs=True,
        refresh_cache=False,
    ):
        self.doc_path = doc_path

        if base_url.startswith("unix:"):
            self.unix_socket = base_url.replace("unix:", "")
            self.base_url = "http://localhost/"
        else:
            self.unix_socket = None
            self.base_url = base_url

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._session = Request(
            url_username=username,
            url_password=password,
            headers=headers,
            validate_certs=validate_certs,
            force_basic_auth=True,
        )

        self.load_api(refresh_cache=refresh_cache)

    def load_api(self, refresh_cache=False):
        # TODO: Find a way to invalidate caches on upstream change
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME") or "~/.cache"
        apidoc_cache = os.path.join(
            os.path.expanduser(xdg_cache_home),
            "squeezer",
            self.base_url.replace(":", "_").replace("/", "_"),
            "api.json",
        )
        try:
            if refresh_cache:
                raise IOError()
            with open(apidoc_cache) as f:
                data = f.read()
            self._parse_api(data)
        except Exception:
            # Try again with a freshly downloaded version
            data = self._download_api()
            self._parse_api(data)
            # Write to cache as it seems to be valid
            makedirs(os.path.dirname(apidoc_cache), exist_ok=True)
            with open(apidoc_cache, "wb") as f:
                f.write(data)

    def _parse_api(self, data):
        self.api_spec = json.loads(data)
        if self.api_spec.get("swagger") == "2.0":
            self.openapi_version = 2
        elif self.api_spec.get("openapi", "").startswith("3."):
            self.openapi_version = 3
        else:
            raise NotImplementedError("Unknown schema version")
        self.operations = {
            method_entry["operationId"]: (method, path)
            for path, path_entry in self.api_spec["paths"].items()
            for method, method_entry in path_entry.items()
            if method
            in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        }

    def _download_api(self):
        return self._session.open(
            "GET", urljoin(self.base_url, self.doc_path), unix_socket=self.unix_socket
        ).read()

    def extract_params(self, param_type, path_spec, method_spec, params):
        param_spec = {
            entry["name"]: entry
            for entry in path_spec.get("parameters", [])
            if entry["in"] == param_type
        }
        param_spec.update(
            {
                entry["name"]: entry
                for entry in method_spec.get("parameters", [])
                if entry["in"] == param_type
            }
        )
        result = {}
        for name in list(params.keys()):
            if name in param_spec:
                param_spec.pop(name)
                result[name] = params.pop(name)
        remaining_required = [
            item["name"] for item in param_spec.values() if item.get("required", False)
        ]
        if any(remaining_required):
            raise Exception(
                "Required parameters [{0}] missing for {1}.".format(
                    ", ".join(remaining_required), param_type
                )
            )
        return result

    def render_body(self, path_spec, method_spec, headers, body=None, uploads=None):
        if not (body or uploads):
            return None
        if self.openapi_version == 2:
            content_types = (
                method_spec.get("consumes")
                or path_spec.get("consumes")
                or self.api_spec.get("consumes")
            )
        else:
            content_types = list(method_spec["requestBody"]["content"].keys())
        if uploads:
            body = body or {}
            if any(
                (
                    content_type.startswith("multipart/form-data")
                    for content_type in content_types
                )
            ):
                boundary = uuid.uuid4().hex
                part_boundary = b"--" + to_bytes(boundary, errors="surrogate_or_strict")

                form = []
                for key, value in body.items():
                    b_key = to_bytes(key, errors="surrogate_or_strict")
                    form.extend(
                        [
                            part_boundary,
                            b'Content-Disposition: form-data; name="%s"' % b_key,
                            b"",
                            to_bytes(value, errors="surrogate_or_strict"),
                        ]
                    )
                for key, file_data in uploads.items():
                    b_key = to_bytes(key, errors="surrogate_or_strict")
                    form.extend(
                        [
                            part_boundary,
                            b'Content-Disposition: file; name="%s"; filename="%s"'
                            % (b_key, b_key),
                            b"Content-Type: application/octet-stream",
                            b"",
                            file_data,
                        ]
                    )
                form.append(part_boundary + b"--")
                data = b"\r\n".join(form)
                headers[
                    "Content-Type"
                ] = "multipart/form-data; boundary={boundary}".format(boundary=boundary)
            else:
                raise Exception("No suitable content type for file upload specified.")
        else:
            if any(
                (
                    content_type.startswith("application/json")
                    for content_type in content_types
                )
            ):
                data = json.dumps(body)
                headers["Content-Type"] = "application/json"
            elif any(
                (
                    content_type.startswith("application/x-www-form-urlencoded")
                    for content_type in content_types
                )
            ):
                data = urlencode(body)
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                raise Exception("No suitable content type for file upload specified.")
        headers["Content-Length"] = len(data)
        return data

    def call(self, operation_id, parameters=None, body=None, uploads=None):
        method, path = self.operations[operation_id]
        path_spec = self.api_spec["paths"][path]
        method_spec = path_spec[method]

        if parameters is None:
            parameters = {}
        else:
            parameters = parameters.copy()

        if any(self.extract_params("cookie", path_spec, method_spec, parameters)):
            raise NotImplementedError("Cookie parameters are not implemented.")

        headers = self.extract_params("header", path_spec, method_spec, parameters)

        for name, value in self.extract_params(
            "path", path_spec, method_spec, parameters
        ).items():
            path = path.replace("{" + name + "}", value)

        query_string = urlencode(
            self.extract_params("query", path_spec, method_spec, parameters), doseq=True
        )

        if any(parameters):
            raise Exception(
                "Parameter [{names}] not available for {operation_id}.".format(
                    names=", ".join(parameters.keys()), operation_id=operation_id
                )
            )
        url = urljoin(self.base_url, path)
        if query_string:
            url += "?" + query_string

        data = self.render_body(path_spec, method_spec, headers, body, uploads)

        result = self._session.open(
            method, url, data=data, headers=headers, unix_socket=self.unix_socket
        ).read()
        if result:
            return json.loads(result)
        return None
