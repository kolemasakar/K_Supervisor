from ksupervisor.extensions import NamedExtensionRegistry


def test_named_extension_registry_supports_templates_and_adapters():
    templates = NamedExtensionRegistry()
    adapters = NamedExtensionRegistry()

    template = object()
    adapter = object()
    templates.register("demo-template", template)
    adapters.register("demo-adapter", adapter)

    assert templates.get("demo-template") is template
    assert adapters.get("demo-adapter") is adapter
    assert templates.names() == ("demo-template",)
    assert adapters.names() == ("demo-adapter",)
