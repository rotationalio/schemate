"""
Schemate profile classes for analyzing and generating JSON schema profiles.
"""

import json

from .serialize import Encoder
from .types import Type, is_base64
from .exceptions import PropertyValueError, PropertyTypeError

from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Union, Any

# If a string is longer than this it is considered a text field.
DEFAULT_TEXT_LIMIT = 256

# If the number of values exceeds this limit then the property is not considered discrete.
DISCRET_VALUES_LIMIT = 50

# Union of all property types that can be inferred from schemaless types.
PropertyType = Union["Property", "ObjectProperty", "ArrayProperty", "AmbiguousProperty"]


@dataclass(init=True, repr=False, eq=True, order=False)
class Profile:
    """
    A profile of a schemaless document or group of documents. The profile contains
    the datatypes of the fields in the documents as well as other information describing
    the fields and their nested properties. The profile can be used to generate a JSON
    schema or another schema format.
    """

    schema: PropertyType
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


def cast(value: Any, text_limit: int = DEFAULT_TEXT_LIMIT) -> PropertyType:
    """
    Cast a value from JSON into a property type. This is the first step in schema
    analysis and is used to determine how to treat the value in the document.
    """
    if value is None:
        return Property(type=Type.NULL, count=1)

    if isinstance(value, bool):
        return Property(type=Type.BOOLEAN, count=1)

    if isinstance(value, int):
        return DiscreteProperty(type=Type.NUMBER, count=1, values={value: 1})

    if isinstance(value, float):
        return Property(type=Type.NUMBER, count=1)

    if isinstance(value, str):
        if len(value) < text_limit:
            return DiscreteProperty(type=Type.STRING, count=1, values={value: 1})
        else:
            if is_base64(value):
                return Property(type=Type.BLOB, count=1)
            return Property(type=Type.TEXT, count=1)

    if isinstance(value, bytes):
        return Property(type=Type.BLOB, count=1)

    if isinstance(value, dict):
        return ObjectProperty(
            type=Type.OBJECT,
            properties={
                k: cast(v) for k, v in value.items()
            },
            count=1,
        )

    if isinstance(value, list):
        # Cast and merge is required to detect the type(s) of the items in the array
        items = [cast(item) for item in value]
        if len(items) == 0:
            return ArrayProperty(type=Type.ARRAY, count=1, items=None)
        if len(items) == 1:
            return ArrayProperty(type=Type.ARRAY, count=1, items=items[0])

        # Merge the items to get the type of the array
        merged = items[0]
        for item in items[1:]:
            merged = merged.merge(item)
        return ArrayProperty(type=Type.ARRAY, count=1, items=merged)


@dataclass(init=True, repr=False, eq=False)
class Property:
    """
    A property describes a field in a document as well as the number of times that
    field appears in the document. This is the base class for all more complex
    properties and is used to describe null, boolean, float, text, and blob type
    properties (e.g. properties that can be counted but don't have sub properties or
    discrete values).
    """

    type: Type
    count: int = 0

    def merge(self, other: PropertyType) -> PropertyType:
        """
        Merges the other property into this property. If the other property is not the
        same type as this property then an ambiguous property will be returned.
        """
        # AmbiguousProperty should not call super()
        if self.type == Type.AMBIGUOUS:
            raise PropertyTypeError("unable to merge into ambiguous property")

        # Handle mismatched type ambiguity
        if self.type != other.type:
            if other.type == Type.AMBIGUOUS:
                return other.merge(self)

            return AmbiguousProperty(
                type=Type.AMBIGUOUS,
                types=[self, other],
                count=self.count + other.count,
            )

        # All base classes should update the left-hand side and return self
        self.count += other.count
        return self

    def truncate(self, limit=DISCRET_VALUES_LIMIT) -> "Property":
        return self

    def __eq__(self, other: PropertyType) -> bool:
        if not isinstance(other, Property):
            return False

        return (
            self.type == other.type and self.count == other.count
        )

    def __repr__(self):
        return f"{self.__class__.__name__}{json.dumps(self, cls=Encoder)}"


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class DiscreteProperty(Property):
    """
    A discrete property describes a field that has a fixed set of values such as
    numbers, or strings (note that booleans are not considered discrete). The
    distribution of each value is tracked so long as the
    """

    unique: int = None
    values: Dict[str | int, int] = field(default_factory=defaultdict(int))

    def __post_init__(self):
        # Ensure the values are a defaultdict
        if not isinstance(self.values, defaultdict):
            if isinstance(self.values, dict):
                self.values = defaultdict(int, self.values)
            else:
                raise PropertyTypeError("values must be a dict or a defaultdict")

        # Ignore unique input and calculate it from the values
        self.unique = len(self.values)

    def merge(self, other: PropertyType) -> PropertyType:
        if self.type == other.type:
            keys = self.values.keys() | other.values.keys()
            for key in keys:
                self.values[key] += other.values[key]
            self.unique = len(self.values)
        return super(DiscreteProperty, self).merge(other)

    def truncate(self, limit=DISCRET_VALUES_LIMIT) -> Union[Property, "DiscreteProperty"]:
        if len(self.values) > limit:
            return Property(
                type=self.type,
                count=self.count
            )
        return self

    def __eq__(self, other):
        if not isinstance(other, DiscreteProperty):
            return False

        if self.values.keys() != other.values.keys():
            return False

        for key, value in self.values.items():
            if value != other.values[key]:
                return False

        return super(DiscreteProperty, self).__eq__(other)


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class AmbiguousProperty(Property):
    """
    An ambiguous property describes a field that has multiple types. All types observed
    are listed under the types list and the count is the number of times that field
    appeared in a document. The sum of the counts of the types should be equal to the
    top level count of the ambiguous property.
    """

    type: Type = Type.AMBIGUOUS
    types: List[PropertyType] = field(default_factory=list)

    def __post_init__(self):
        self.validate()

    def merge(self, other):
        # Merge both ambiguous types together.
        # Note an ambiguous type cannot contain an ambiguous type.
        if self.type == other.type:
            for item in other.types:
                if item.type == self.type:
                    raise PropertyValueError(
                        "an ambiguous property cannot contain another ambiguous property"
                    )
                self.merge(item)

        # Merge a non-ambiguous type into an ambiguous one.
        else:
            for item in self.types:
                if item.type == other.type:
                    item.merge(other)
                    break
            else:
                self.types.append(other)

            # Cannot call super here to avoid creating another ambiguous property
            self.count += other.count

        # Make sure the merge is validated
        self.validate()
        return self

    def truncate(self, limit=DISCRET_VALUES_LIMIT) -> "AmbiguousProperty":
        self.types = [
            item.truncate(limit) for item in self.types
        ]
        self.validate()
        return self

    def __eq__(self, other):
        # Only valid types can be compared.
        self.validate()

        if not isinstance(other, AmbiguousProperty):
            return False

        # Ensure the other ambiguous property is valid
        other.validate()

        # Order doesn't matter for equality
        if len(self.types) != len(other.types):
            return False

        for item in self.types:
            for cmpt in other.types:
                if item.type == cmpt.type:
                    if item != cmpt:
                        return False
                    break
            else:
                return False

        return super(AmbiguousProperty, self).__eq__(other)

    def validate(self):
        types = [t.type for t in self.types]
        if len(self.types) != len(set(types)):
            raise PropertyValueError(
                "ambiguous property contains duplicate types"
            )

        if Type.AMBIGUOUS in types:
            raise PropertyValueError(
                "an ambiguous property cannot contain another ambiguous property"
            )


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class ObjectProperty(Property):
    """
    Allows nested properties to be defined for a document or for fields in the document.
    The properties are defined as a dictionary of field names to their properties. The
    count is the number of times the field appeared in a document.
    """

    type: Type = Type.OBJECT
    properties: Dict[str, PropertyType] = field(default_factory=dict)

    def merge(self, other):
        if self.type == other.type:
            # Merge the properties of the other object into this one
            for key, prop in other.properties.items():
                if key in self.properties:
                    self.properties[key].merge(prop)
                else:
                    self.properties[key] = prop

        return super(ObjectProperty, self).merge(other)

    def truncate(self, limit=DISCRET_VALUES_LIMIT) -> "ObjectProperty":
        for key, prop in self.properties.items():
            self.properties[key] = prop.truncate(limit)
        return self

    def __eq__(self, other):
        if not isinstance(other, ObjectProperty):
            return False

        if self.properties.keys() != other.properties.keys():
            return False

        for key, value in self.properties.items():
            if value != other.properties[key]:
                return False

        return super(ObjectProperty, self).__eq__(other)


@dataclass(init=True, repr=False, eq=False, kw_only=True)
class ArrayProperty(Property):
    """
    Allows for a property to be a list and define what the properties are of each of
    the items in the list. If the array has multiple types then it will be an
    AmbiguousProperty that describes each of the items in the array.
    """

    type: Type = Type.ARRAY
    items: PropertyType

    def merge(self, other):
        if self.type == other.type:
            if self.items is None:
                self.items = other.items
            elif other.items is not None:
                self.items.merge(other.items)
        return super(ArrayProperty, self).merge(other)

    def truncate(self, limit=DISCRET_VALUES_LIMIT) -> "ArrayProperty":
        self.items = self.items.truncate(limit)
        return self

    def __eq__(self, other):
        if not isinstance(other, ArrayProperty):
            return False

        if self.items != other.items:
            return False

        return super(ArrayProperty, self).__eq__(other)
