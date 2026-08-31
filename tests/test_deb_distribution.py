from ansible_collections.pulp.squeezer.plugins.modules import deb_distribution


class FakeModule:
    def __init__(self, repository):
        self.params = {
            "name": "test_deb_distribution",
            "base_path": "test_deb_base_path",
            "publication": None,
            "repository": repository,
            "content_guard": None,
        }
        self.pulp_ctx = object()
        self.process_args = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def process(self, natural_key, desired_attributes):
        self.process_args = (natural_key, desired_attributes)


def test_repository_distribution_resolves_repository_name(monkeypatch):
    module = FakeModule("test_deb_repository")
    module_kwargs = {}

    def module_factory(**kwargs):
        module_kwargs.update(kwargs)
        return module

    class FakeRepositoryContext:
        def __init__(self, pulp_ctx, entity):
            assert pulp_ctx is module.pulp_ctx
            assert entity == {"name": "test_deb_repository"}
            self.pulp_href = "/pulp/api/v3/repositories/deb/apt/test/"

    monkeypatch.setattr(deb_distribution, "PulpEntityAnsibleModule", module_factory)
    monkeypatch.setattr(deb_distribution, "PulpAptRepositoryContext", FakeRepositoryContext)

    deb_distribution.main()

    assert module_kwargs["mutually_exclusive"] == [("publication", "repository")]
    assert module.process_args == (
        {"name": "test_deb_distribution"},
        {
            "base_path": "test_deb_base_path",
            "repository": "/pulp/api/v3/repositories/deb/apt/test/",
        },
    )


def test_repository_distribution_can_clear_repository(monkeypatch):
    module = FakeModule("")
    monkeypatch.setattr(deb_distribution, "PulpEntityAnsibleModule", lambda **_kwargs: module)

    deb_distribution.main()

    assert module.process_args == (
        {"name": "test_deb_distribution"},
        {"base_path": "test_deb_base_path", "repository": ""},
    )
