class RegistryError(RuntimeError):
    pass


class DuplicateRegistrationError(RegistryError):
    pass


class RegistryConflictError(RegistryError):
    pass


class CapabilityResolutionError(RegistryError):
    pass
