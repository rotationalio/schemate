"""
Schemate exception hierarchy
"""


class SchemateException(Exception):
    """Base class for all Schemate exceptions."""
    pass


class CommandError(SchemateException):
    """CLI errors that are printed without a traceback."""
    pass


class ConfigLoadError(SchemateException, ValueError):
    pass


class InvalidConfiguration(SchemateException):
    pass


class LoaderError(SchemateException):
    """Errors related to data loaders."""
    pass


class UnsupportedLoader(LoaderError, ValueError):
    pass


class PropertyTypeError(SchemateException, TypeError):
    pass


class PropertyValueError(SchemateException, ValueError):
    pass
