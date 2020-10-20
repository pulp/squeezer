#!/usr/bin/env python

import os
import sys
import vcr
import json
import re

try:
    from urlparse import urlparse, urlunparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, urlunparse, parse_qs


def safe_method_matcher(r1, r2):
    assert r1.method not in [
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ], "Method {0} not allowed in check_mode".format(r1.method)
    assert r1.method == r2.method


# We need our own json level2 matcher, because, python2 and python3 do not save
# dictionaries in the same order.
# Also multipart bounderies must be ignored.
def amp_body_matcher(r1, r2):
    c1 = r1.headers.get("content-type")
    c2 = r2.headers.get("content-type")
    if c1 == "application/json" and c2 == "application/json":
        if r1.body is None or r2.body is None:
            return r1.body == r2.body
        body1 = json.loads(r1.body.decode("utf8"))
        body2 = json.loads(r2.body.decode("utf8"))
        if "search" in body1:
            body1["search"] = ",".join(
                sorted(re.findall(r'([^=,]*="(?:[^"]|\\")*")', body1["search"]))
            )
        if "search" in body2:
            body2["search"] = ",".join(
                sorted(re.findall(r'([^=,]*="(?:[^"]|\\")*")', body2["search"]))
            )
        return body1 == body2
    elif c1.startswith("application/x-www-form-urlencoded") and c2.startswith(
        "application/x-www-form-urlencoded"
    ):
        return parse_qs(r1.body) == parse_qs(r1.body)
    elif c1.startswith("multipart/form-data") and c2.startswith("multipart/form-data"):
        if r1.body is None or r2.body is None:
            return r1.body == r2.body
        boundary1 = re.findall(r"boundary=(\S.*)", r1.headers["content-type"])[
            0
        ].encode()
        boundary2 = re.findall(r"boundary=(\S.*)", r2.headers["content-type"])[
            0
        ].encode()
        return r1.body.replace(boundary1, b"TILT") == r2.body.replace(
            boundary2, b"TILT"
        )
    else:
        return r1.body == r2.body


def filter_request_uri(request):
    request.uri = urlunparse(urlparse(request.uri)._replace(netloc="pulp.example.org"))
    return request


VCR_PARAMS_FILE = os.environ.get("PAM_TEST_VCR_PARAMS_FILE")

# Remove the name of the wrapper from argv
# (to make it look like the module had been called directly)
sys.argv.pop(0)

if VCR_PARAMS_FILE is None:
    # Run the program as if nothing had happened
    with open(sys.argv[0]) as f:
        code = compile(f.read(), sys.argv[0], "exec")
        exec(code)
else:
    # Run the program wrapped within vcr cassette recorder
    # Load recording parameters from file
    with open(VCR_PARAMS_FILE, "r") as params_file:
        test_params = json.load(params_file)
    cassette_file = "../fixtures/{}-{}.yml".format(
        test_params["test_name"], test_params["serial"]
    )
    # Increase serial and dump back to file
    test_params["serial"] += 1
    with open(VCR_PARAMS_FILE, "w") as params_file:
        json.dump(test_params, params_file)

    # Call the original python script with vcr-cassette in place
    amp_vcr = vcr.VCR()

    method_matcher = "method"
    if test_params["check_mode"]:
        amp_vcr.register_matcher("safe_method_matcher", safe_method_matcher)
        method_matcher = "safe_method_matcher"

    amp_vcr.register_matcher("amp_body", amp_body_matcher)

    with amp_vcr.use_cassette(
        cassette_file,
        record_mode=test_params["record_mode"],
        match_on=[method_matcher, "path", "query", "amp_body"],
        filter_headers=["Authorization"],
        before_record_request=filter_request_uri,
    ):
        with open(sys.argv[0]) as f:
            code = compile(f.read(), sys.argv[0], "exec")
            exec(code)
