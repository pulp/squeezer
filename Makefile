NAMESPACE := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["namespace"])')
NAME := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["name"])')
VERSION := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["version"])')
MANIFEST := build/collections/ansible_collections/$(NAMESPACE)/$(NAME)/MANIFEST.json

PLUGIN_TYPES := $(filter-out __%,$(notdir $(wildcard plugins/*)))
METADATA := galaxy.yml LICENSE README.md
$(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),$(eval _$(PLUGIN_TYPE) := $(filter-out %__init__.py,$(wildcard plugins/$(PLUGIN_TYPE)/*.py))))
DEPENDENCIES := $(METADATA) $(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),$(_$(PLUGIN_TYPE)))

PYTHON_VERSION = $(shell python -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
COLLECTION_COMMAND ?= ansible-galaxy
SANITY_OPTS =
TEST =
PYTEST = pytest -n 4 --boxed -v

default: help
help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help           to show this message"
	@echo "  info           to show infos about the collection"
	@echo "  lint           to run code linting"
	@echo "  test           to run unit tests"
	@echo "  sanity         to run santy tests"
	@echo "  setup          to set up test, lint"
	@echo "  test-setup     to install test dependencies"
	@echo "  test_<test>    to run a specific unittest"
	@echo "  record_<test>  to (re-)record the server answers for a specific test"
	@echo "  clean_<test>   to run a specific test playbook with the teardown and cleanup tags"
	@echo "  dist           to build the collection artifact"

info:
	@echo "Building collection $(NAMESPACE)-$(NAME)-$(VERSION)"
	@echo $(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),"\n  $(PLUGIN_TYPE): $(basename $(notdir $(_$(PLUGIN_TYPE))))")

lint: $(MANIFEST) | tests/playbooks/vars/server.yaml
	yamllint -f parsable tests/playbooks
	ansible-playbook --syntax-check tests/playbooks/*.yaml | grep -v '^$$'
	black . --diff --check

sanity: $(MANIFEST) | tests/playbooks/vars/server.yaml
	# Fake a fresh git repo for ansible-test
	cd $(<D) ; git init ; echo tests > .gitignore ; ansible-test sanity $(SANITY_OPTS) --python $(PYTHON_VERSION)

test: $(MANIFEST) | tests/playbooks/vars/server.yaml
	$(PYTEST) $(TEST)

test_%: FORCE $(MANIFEST) | tests/playbooks/vars/server.yaml
	pytest -v 'tests/test_playbooks.py::test_playbook[$*]' 'tests/test_playbooks.py::test_check_mode[$*]'

record_%: FORCE $(MANIFEST)
	$(RM) tests/fixtures/$*-*.yml
	pytest -v 'tests/test_playbooks.py::test_playbook[$*]' --record

clean_%: FORCE $(MANIFEST) | tests/playbooks/vars/server.yaml
	ansible-playbook --tags teardown,cleanup -i tests/inventory/hosts 'tests/playbooks/$*.yaml'

test-setup: requirements.txt | tests/playbooks/vars/server.yaml
	pip install --upgrade pip
	pip install -r requirements.txt

tests/playbooks/vars/server.yaml:
	cp $@.example $@
	@echo "For recording, please adjust $@ to match your reference server."

$(MANIFEST): $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
ifeq ($(COLLECTION_COMMAND),mazer)
	# No idea, why this fails. But mazer is old and deprecated so unlikely to beeing fixed...
	# mazer install --collections-path build/collections $<
	-mkdir build/collections build/collections/ansible_collections build/collections/ansible_collections/$(NAMESPACE) build/collections/ansible_collections/$(NAMESPACE)/$(NAME)
	tar xf $< -C build/collections/ansible_collections/$(NAMESPACE)/$(NAME)
else
	ansible-galaxy collection install -p build/collections $< --force
endif

build/src/%: % | build
	cp $< $@

build:
	-mkdir build build/src build/src/plugins $(addprefix build/src/plugins/,$(PLUGIN_TYPES))

$(NAMESPACE)-$(NAME)-$(VERSION).tar.gz: $(addprefix build/src/,$(DEPENDENCIES)) | build
ifeq ($(COLLECTION_COMMAND),mazer)
	mazer build --collection-path=build/src
	cp build/src/releases/$@ .
else
	ansible-galaxy collection build build/src --force
endif

dist: $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz

publish: $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	ansible-galaxy collection publish --api-key $(GALAXY_API_KEY) $<

clean:
	rm -rf build

FORCE:

.PHONY: help dist lint sanity test test-setup publish FORCE
