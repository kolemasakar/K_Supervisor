from .config import PlatformConfig, load_config
from .extensions import (
    EXTENSION_GROUPS,
    DiscoveredExtension,
    ExtensionContext,
    activate_extension,
    discover_extensions,
)

__version__ = "0.1.0"

__all__ = [
    "EXTENSION_GROUPS",
    "DiscoveredExtension",
    "ExtensionContext",
    "PlatformConfig",
    "activate_extension",
    "discover_extensions",
    "load_config",
]
