import os
import pytest
import subprocess


def pytest_addoption(parser):
    parser.addoption(
        "--vcrmode",
        action="store",
        default="replay",
        choices=["replay", "record", "live"],
        help="mode for vcr recording; one of ['replay', 'record', 'live']",
    )


@pytest.fixture
def vcrmode(request):
    return request.config.getoption("vcrmode")


if "PULP_LOGGING" in os.environ:

    @pytest.fixture
    def pulp_container_log(vcrmode):
        if vcrmode == "live":
            with subprocess.Popen(
                [
                    os.environ["PULP_LOGGING"],
                    "logs",
                    "-f",
                    "--tail",
                    "0",
                    "pulp-ephemeral",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) as proc:
                yield
                proc.kill()
                print(proc.stdout.read().decode())
        else:
            yield

else:

    @pytest.fixture
    def pulp_container_log():
        yield
