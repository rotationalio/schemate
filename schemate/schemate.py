"""
Schemate profile classes for analyzing and generating JSON schema profiles.
"""

import json

from .types import Type
from .serialize import Encoder

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union


Properties = Union["Property", "ObjectProperty", "ArrayProperty", "AmbiguousProperty"]


@dataclass(init=True, repr=False, eq=True, order=False)
class Profile:
    """
    A profile of a schemaless document or group of documents. The profile contains
    the datatypes of the fields in the documents as well as other information describing
    the fields and their nested properties. The profile can be used to generate a JSON
    schema or another schema format.
    """

    schema: Properties
    documents: int = 0
    ambiguous: int = 0

    def dump(self, fp, **kwargs):
        """
        Dumps the profile as a JSON document using the json.dump arguments.
        """
        if "cls" not in kwargs:
            kwargs["cls"] = Encoder
        return json.dump(self, fp, **kwargs)

    def dumps(self, *args, **kwargs):
        """
        Dumps the profile as a JSON string using the json.dumps arguments.
        """
        if "cls" not in kwargs:
            kwargs["cls"] = Encoder
        return json.dumps(self, **kwargs)


@dataclass(init=True, repr=False, eq=False)
class Property:
    """
    A property describes a field in a document as well as the number of times that
    field appears in the document and if the field is a number or a string, the number
    of unique values in that field. Note that only strings < 255 characters are tracked
    for uniqueness.
    """

    type: Type
    count: int = 0
    unique: Optional[int] = 0


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class AmbiguousProperty(Property):
    """
    An ambiguous property describes a field that has multiple types. All types observed
    are listed under the types list and the count is the number of times that field
    appeared in a document. The sum of the counts of the types should be equal to the
    top level count of the ambiguous property.
    """

    type: Type = Type.AMBIGUOUS
    types: List[Properties] = field(default_factory=list)


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class ObjectProperty(Property):
    """
    Allows nested properties to be defined for a document or for fields in the document.
    The properties are defined as a dictionary of field names to their properties. The
    count is the number of times the field appeared in a document.
    """

    type: Type = Type.OBJECT
    properties: Dict[str, Properties] = field(default_factory=dict)


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class ArrayProperty(Property):
    """
    Allows for a property to be a list and define what the properties are of each of
    the items in the list. If the array has multiple types then it will be an
    AmbiguousProperty that describes each of the items in the array.
    """

    type: Type = Type.ARRAY
    items: Properties
