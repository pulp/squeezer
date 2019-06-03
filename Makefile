default: help
help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help           to show this message"
	@echo "  lint           to run flake8 and pylint"
	@echo "  test           to run unit tests"
	@echo "  test-setup     to install test dependencies"
	@echo "  test_<test>    to run a specific unittest"
	@echo "  record_<test>  to (re-)record the server answers for a specific test"
	@echo "  clean_<test>   to run a specific test playbook with the teardown and cleanup tags"

lint:
	pycodestyle --ignore=E402,E722 --max-line-length=160 plugins/modules plugins/module_utils test

test:
	pytest

test_%: FORCE
	pytest 'test/test_crud.py::test_crud[$*]'

record_%: FORCE
	$(RM) test/fixtures/$*-*.yml
	pytest 'test/test_crud.py::test_crud[$*]' --record

clean_%: FORCE
	ansible-playbook --tags teardown,cleanup -i test/inventory/hosts 'test/test_playbooks/$*.yaml'

test-setup: test/test_playbooks/vars/server.yaml
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r test/requirements.txt

test/test_playbooks/vars/server.yaml:
	cp test/test_playbooks/vars/server.yaml.example test/test_playbooks/vars/server.yaml
	@echo "For recording, please adjust test/test_playbooks/vars/server.yaml to match your reference server."

FORCE:

.PHONY: help lint sanity test test-setup FORCE
