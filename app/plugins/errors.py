class PluginError(Exception):
    """Base exception for plugin foundation failures."""


class PluginManifestError(PluginError):
    """Raised when plugin manifest validation fails."""


class PluginPermissionError(PluginError):
    """Raised when a plugin asks for an unknown or forbidden permission."""


class PluginRegistryError(PluginError):
    """Raised when plugin registry operations fail."""


class PluginSandboxError(PluginError):
    """Raised when sandbox policy blocks an operation."""


class PluginLoaderError(PluginError):
    """Raised when safe plugin loading or manifest inspection fails."""
