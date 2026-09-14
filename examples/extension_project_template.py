from factory.contracts import BootstrapFile


def minimal_template(spec, target):
    return (
        BootstrapFile("README.md", f"# {spec.name}\n"),
        BootstrapFile("docs/ARCHITECTURE.md", "# ARCHITECTURE\n"),
    )


def register(context):
    registry = context.require("project_templates")
    registry.register("minimal", minimal_template)
    return "minimal"
