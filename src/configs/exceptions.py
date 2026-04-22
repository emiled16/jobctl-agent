class ConfigError(Exception):
    """Base error for invalid or missing jobctl configuration."""


class ProjectNotFoundError(ConfigError):
    """Raised when no .jobctl project directory exists above a path."""


class ConfigValidationError(ConfigError):
    """Raised when config.yaml is missing required fields or has invalid data."""
