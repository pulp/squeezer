NAMESPACE := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["namespace"])')
NAME := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["name"])')
VERSION := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["version"])')
MANIFEST := build/collections/ansible_collections/$(NAMESPACE)/$(NAME)/MANIFEST.json

ROLES := $(wildcard roles/*)
PLUGIN_TYPES := $(filter-out __%,$(notdir $(wildcard plugins/*)))
METADATA := galaxy.yml LICENSE README.md meta/runtime.yml
$(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),$(eval _$(PLUGIN_TYPE) := $(filter-out %__init__.py,$(wildcard plugins/$(PLUGIN_TYPE)/*.py))))
DEPENDENCIES := $(METADATA) $(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),$(_$(PLUGIN_TYPE))) $(foreach ROLE,$(ROLES),$(wildcard $(ROLE)/*/*)) $(foreach ROLE,$(ROLES),$(ROLE)/README.md)

PYTHON_VERSION = $(shell python -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
SANITY_OPTS =
TEST =
PYTEST = pytest -n 4 -v

ACTION_GROUPS := $(shell python -c 'import yaml; print("".join(yaml.safe_load(open("meta/runtime.yml"))["action_groups"]["squeezer"]))')
MODULES := $(shell python -c 'import os; print("".join([os.path.splitext(f)[0] for f in sorted(os.listdir("plugins/modules/"))]))')

default: help
help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help             to show this message"
	@echo "  info             to show infos about the collection"
	@echo "  lint             to run code linting"
	@echo "  test             to run unit tests"
	@echo "  livetest         to run test playbooks live (without vcr)"
	@echo "  sanity           to run santy tests"
	@echo "  setup            to set up test, lint"
	@echo "  test-setup       to install test dependencies"
	@echo "  test_<test>      to run a specific unittest"
	@echo "  livetest_<test>  to run a specific unittest live (without vcr)"
	@echo "  record_<test>    to (re-)record the server answers for a specific test"
	@echo "  clean_<test>     to run a specific test playbook with the teardown and cleanup tags"
	@echo "  dist             to build the collection artifact"

info:
	@echo "Building collection $(NAMESPACE)-$(NAME)-$(VERSION)"
	@echo "  roles:\n $(foreach ROLE,$(notdir $(ROLES)),   - $(ROLE)\n)"
	@echo " $(foreach PLUGIN_TYPE,$(PLUGIN_TYPES), $(PLUGIN_TYPE):\n $(foreach PLUGIN,$(basename $(notdir $(_$(PLUGIN_TYPE)))),   - $(PLUGIN)\n)\n)"

black:
	isort .
	black .

lint: $(MANIFEST) | tests/playbooks/vars/server.yaml
	yamllint -f parsable tests/playbooks
	ansible-playbook --syntax-check tests/playbooks/*.yaml | grep -v '^$$'
	black --check --diff .
	isort -c --diff .
ifneq ($(ACTION_GROUPS), $(MODULES))
	@echo 'plugins/modules/ and meta/runtime.yml action_groups are not in sync' && exit 1
endif
	GALAXY_IMPORTER_CONFIG=tests/galaxy-importer.cfg python -m galaxy_importer.main $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	@echo "🙊 Code 🙉 LGTM 🙈"

sanity: $(MANIFEST) | tests/playbooks/vars/server.yaml
	# Fake a fresh git repo for ansible-test
	cd $(<D) ; git init ; echo tests > .gitignore ; ansible-test sanity $(SANITY_OPTS) --python $(PYTHON_VERSION)

test: $(MANIFEST) | tests/playbooks/vars/server.yaml
	$(PYTEST) $(TEST)

livetest: $(MANIFEST) | tests/playbooks/vars/server.yaml
	pytest -v 'tests/test_playbooks.py::test_playbook' --vcrmode live

test_%: FORCE $(MANIFEST) | tests/playbooks/vars/server.yaml
	pytest -v 'tests/test_playbooks.py::test_playbook[$*]' 'tests/test_playbooks.py::test_check_mode[$*]'

livetest_%: FORCE $(MANIFEST) | tests/playbooks/vars/server.yaml
	pytest -v 'tests/test_playbooks.py::test_playbook[$*]' --vcrmode live

record_%: FORCE $(MANIFEST)
	$(RM) tests/fixtures/$*-*.yml
	pytest -v 'tests/test_playbooks.py::test_playbook[$*]' --vcrmode record

clean_%: FORCE $(MANIFEST) | tests/playbooks/vars/server.yaml
	ansible-playbook --tags teardown,cleanup -i tests/inventory/hosts 'tests/playbooks/$*.yaml'

test-setup: requirements.txt | tests/playbooks/vars/server.yaml
	pip install --upgrade pip
	pip install -r requirements.txt

test-setup-lower-bounds: requirements.txt lower_bounds_constraints.lock | tests/playbooks/vars/server.yaml
	pip install --upgrade pip
	pip install -r requirements.txt -c lower_bounds_constraints.lock

tests/playbooks/vars/server.yaml:
	cp $@.example $@
	@echo "For recording, please adjust $@ to match your reference server."

$(MANIFEST): $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	ansible-galaxy collection install -p build/collections $< --force

build/src/%: %
	install -m 644 -DT $< $@

$(NAMESPACE)-$(NAME)-$(VERSION).tar.gz: $(addprefix build/src/,$(DEPENDENCIES))
	ansible-galaxy collection build build/src --force

dist: $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz

install: $(MANIFEST)

publish: $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	ansible-galaxy collection publish --api-key $(GALAXY_API_KEY) $<

clean:
	rm -rf build

FORCE:

.PHONY: help dist install black lint sanity test livetest test-setup publish FORCE
