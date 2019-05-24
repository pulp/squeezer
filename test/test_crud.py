import pytest
import os
import sys
import tempfile
import json
import ansible_runner


TEST_NAMES = [name[:-5] for name in os.listdir('test/test_playbooks') if name.endswith('.yaml')]


# Clean environment from anything that could cause encoding problems
if sys.version_info[0] == 2:
    for envvar in os.environ.keys():
        try:
            os.environ[envvar] = os.environ[envvar].decode('utf-8').encode('ascii', 'ignore')
        except UnicodeError:
            os.environ.pop(envvar)


def run_playbook_vcr(test_name, extra_vars=None, record=False):
    playbook = test_name + '.yaml'
    if extra_vars is None:
        extra_vars = {}
    limit = None
    if record:
        # Cassettes that are to be overwritten must be deleted first
        record_mode = 'once'
        extra_vars['recording'] = True
    else:
        # Never reach out to the internet
        record_mode = 'none'
        # Only run the tests (skip fixtures)
        limit = '!fixtures'

    # Dump recording parameters to json-file and pass its name by environment
    test_params = {'test_name': test_name, 'serial': 0, 'record_mode': record_mode}
    with tempfile.NamedTemporaryFile('w', suffix='json', prefix='fam-vcr-') as params_file:
        json.dump(test_params, params_file.file)
        params_file.file.close()
        os.environ['PAM_TEST_VCR_PARAMS_FILE'] = params_file.name
        return run_playbook(playbook, extra_vars=extra_vars, limit=limit)


def run_playbook(playbook, extra_vars=None, limit=None):
    # Assemble parameters for playbook call
    os.environ['ANSIBLE_CONFIG'] = os.path.join(os.getcwd(), 'ansible.cfg')
    playbook_path = os.path.join(os.getcwd(), 'test', 'test_playbooks', playbook)
    inventory_path = os.path.join(os.getcwd(), 'test', 'inventory', 'hosts')
    return ansible_runner.run(extravars=extra_vars, playbook=playbook_path, limit=limit, verbosity=4, inventory=inventory_path)


@pytest.mark.parametrize('test_name', TEST_NAMES)
def test_crud(test_name, record):
    run = run_playbook_vcr(test_name, record=record)
    print(run.stdout.read())
    assert run.rc == 0
