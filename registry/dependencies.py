from integrations import AvailabilityState, DependencyRequirement, IntegrationKind


def dependency_available(dependency: DependencyRequirement, tools, providers) -> bool:
    registry = tools if dependency.kind == IntegrationKind.TOOL else providers
    component = registry.resolve(dependency.component_id, dependency.version_constraint)
    return component is not None and component.check_availability().state != AvailabilityState.UNAVAILABLE
