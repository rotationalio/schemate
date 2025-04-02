from enum import StrEnum, unique


@unique
class Type(StrEnum):

    NULL = "null"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NUMBER = "number"
    STRING = "string"
    AMBIGUOUS = "ambiguous"
