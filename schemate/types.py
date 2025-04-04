"""
Schemaless types for analyzing documents.
"""

import base64

from enum import StrEnum, unique


@unique
class Type(StrEnum):

    NULL = "null"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NUMBER = "number"
    STRING = "string"
    TEXT = "text"
    BLOB = "blob"
    AMBIGUOUS = "ambiguous"


def is_base64(sb: str | bytes) -> bool:
    """
    Check if the value is a correctly encoded base64 encoded string.

    Parameters
    ----------
    value : str
        The value to check.

    Returns
    -------
    bool
        True if the value is a base64 encoded string, False otherwise.
    """
    # Empty strings are not considered base64
    if not sb:
        return False

    try:
        if isinstance(sb, str):
            sb = bytes(sb, "ascii")

        if not isinstance(sb, bytes):
            raise ValueError("argument must be a string or bytes")

        return base64.b64encode(base64.b64decode(sb)) == sb
    except Exception:
        return False
