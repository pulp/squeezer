NAMESPACE := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["namespace"])')
NAME := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["name"])')
VERSION := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["version"])')
MANIFEST := build/collections/ansible_collections/$(NAMESPACE)/$(NAME)/MANIFEST.json

MODULES := $(shell find plugins/modules -name *.py)
MODULE_UTILS := $(shell find plugins/module_utils -name *.py)
DOC_FRAGMENTS := $(shell find plugins/doc_fragments -name *.py)

PYTHON_VERSION = 3.7

default: help
help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help           to show this message"
	@echo "  info           to show infos about the collection"
	@echo "  lint           to run code linting"
	@echo "  test           to run unit tests"
	@echo "  test-setup     to install test dependencies"
	@echo "  test_<test>    to run a specific unittest"
	@echo "  record_<test>  to (re-)record the server answers for a specific test"
	@echo "  clean_<test>   to run a specific test playbook with the teardown and cleanup tags"

info:
	@echo Building collection $(NAMESPACE)-$(NAME)-$(VERSION)
	@echo   modules: $(MODULES)
	@echo   module_utils: $(MODULE_UTILS)
	@echo   doc_fragments: $(DOC_FRAGMENTS)

lint: $(MANIFEST)
	yamllint -f parsable tests/playbooks
	ansible-playbook --syntax-check tests/playbooks/*.yaml | grep -v '^$$'
	flake8 --ignore=E402 --max-line-length=160 plugins tests

sanity: $(MANIFEST)
	# Fake a fresh git repo for ansible-test
	cd $(<D) ; git init ; echo tests > .gitignore ; ansible-test sanity --local --python $(PYTHON_VERSION)

test: $(MANIFEST)
	pytest -v tests

test_%: FORCE $(MANIFEST)
	pytest 'tests/test_playbooks.py::test_playbook[$*]' 'tests/test_playbooks.py::test_check_mode[$*]'

record_%: FORCE $(MANIFEST)
	$(RM) tests/fixtures/$*-*.yml
	pytest 'tests/test_playbooks.py::test_playbook[$*]' --record

clean_%: FORCE $(MANIFEST)
	ansible-playbook --tags teardown,cleanup -i tests/inventory/hosts 'tests/playbooks/$*.yaml'

test-setup: tests/playbooks/vars/server.yaml
	pip install --upgrade pip
	pip install -r requirements.txt

tests/playbooks/vars/server.yaml:
	cp tests/playbooks/vars/server.yaml.example tests/playbooks/vars/server.yaml
	@echo "For recording, please adjust tests/playbooks/vars/server.yaml to match your reference server."

$(MANIFEST): $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	ansible-galaxy collection install -p build/collections $+ --force

$(NAMESPACE)-$(NAME)-$(VERSION).tar.gz: galaxy.yml LICENSE README.md  $(MODULES) $(MODULE_UTILS) $(DOC_FRAGMENTS)
	mkdir -p build/src
	cp galaxy.yml LICENSE README.md build/src
	cp -r plugins build/src
	ansible-galaxy collection build build/src --force

clean:
	rm -rf build

FORCE:

.PHONY: help lint sanity test test-setup FORCE
