from pathlib import Path
from runpy import run_path

from ksupervisor.extensions import ExtensionContext, NamedExtensionRegistry


def test_example_workflow_builds_valid_contract():
    module = run_path(str(Path("examples/workflow_definition.py")))
    workflow = module["build_example_workflow"]()
    assert workflow.workflow_id == "example.research_report"
    assert workflow.start_node_id == "research"


def test_example_project_template_registers_without_supervisor_change():
    module = run_path(str(Path("examples/extension_project_template.py")))
    registry = NamedExtensionRegistry()
    context = ExtensionContext({"project_templates": registry})
    assert module["register"](context) == "minimal"
    assert registry.names() == ("minimal",)
