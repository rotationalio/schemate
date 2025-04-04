"""
Tests the schemate property analysis classes.
"""

import json
import pytest
import base64

from io import StringIO
from schemate.schemate import *
from schemate.exceptions import *
from collections import namedtuple


def test_profile_dump():
    """
    Test profile serialization to JSON format.
    """
    profile = Profile(
        schema=ObjectProperty(properties={
            "available": Property(type="boolean", count=10),
            "color": DiscreteProperty(type="string", count=10, values={"red": 5, "blue": 5}),
            "size": DiscreteProperty(type="number", count=10, values={1: 3, 2: 3, 3: 1}),
            "names": ArrayProperty(
                items=Property(type="string", count=10),
                count=7,
            ),
            "tags": AmbiguousProperty(
                types=[
                    Property(type="string", count=5),
                    ObjectProperty(
                        properties={
                            "key": Property(type="string", count=5),
                            "value": Property(type="string", count=5),
                        },
                        count=5,
                    ),
                ],
                count=10,
            ),
        }, count=10),
        documents=10,
        ambiguous=1,
    )

    expected = {
        "schema": {
            "type": "object",
            "count": 10,
            "properties": {
                "available": {
                    "type": "boolean",
                    "count": 10,
                },
                "color": {
                    "type": "string",
                    "count": 10,
                    "unique": 2,
                    "values": {
                        "red": 5,
                        "blue": 5,
                    },
                },
                "size": {
                    "type": "number",
                    "count": 10,
                    "unique": 3,
                    "values": {
                        "1": 3,
                        "2": 3,
                        "3": 1,
                    },
                },
                "names": {
                    "type": "array",
                    "count": 7,
                    "items": {
                        "type": "string",
                        "count": 10,
                    },
                },
                "tags": {
                    "type": "ambiguous",
                    "count": 10,
                    "types": [
                        {
                            "type": "string",
                            "count": 5,
                        },
                        {
                            "type": "object",
                            "properties": {
                                "key": {
                                    "type": "string",
                                    "count": 5,
                                },
                                "value": {
                                    "type": "string",
                                    "count": 5,
                                },
                            },
                            "count": 5,
                        },
                    ],
                },
            },
        },
        "documents": 10,
        "ambiguous": 1,
    }

    result = profile.dumps()
    assert json.loads(result) == expected

    fp = StringIO()
    profile.dump(fp)
    fp.seek(0)
    result = json.load(fp)
    assert result == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, Property(type="null", count=1)),
        (True, Property(type="boolean", count=1)),
        (False, Property(type="boolean", count=1)),
        (1, DiscreteProperty(type="number", count=1, values={1: 1})),
        (2.0, Property(type="number", count=1)),
        ("hello", DiscreteProperty(type="string", count=1, values={"hello": 1})),
        (
            "This is a very long piece of text that is over two hundred and fifty five characters long. It has more text inside of it than you can shake a stick at. A milkshake would be delicious right now but instead I have to keep typing this extra long string. It's long enough now.",
            Property(type="text", count=1),
        ),
        (
            base64.b64encode(b"This is a very long piece of text that is over two hundred and fifty five characters long. It has more text inside of it than you can shake a stick at. A milkshake would be delicious right now but instead I have to keep typing this extra long string. It's long enough now.").decode('ascii'),
            Property(type="blob", count=1),
        ),
        (
            base64.b64decode(
                "TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseSAtLQ=="
            ),
            Property(type="blob", count=1),
        ),
        (
            {"key": "value"},
            ObjectProperty(
                type="object",
                properties={
                    "key": DiscreteProperty(
                        type="string", count=1, values={"value": 1}
                    ),
                },
                count=1,
            ),
        ),
        (
            ["red", "green", "blue", "red"],
            ArrayProperty(
                items=DiscreteProperty(
                    type="string",
                    count=4,
                    unique=3,
                    values={"red": 2, "green": 1, "blue": 1},
                ),
                count=1,
            ),
        ),
        ([], ArrayProperty(items=None, count=1)),
        ([13.1321], ArrayProperty(items=Property(type="number", count=1), count=1)),
    ],
)
def test_cast(value, expected):
    """
    Test casting a value to a property type.
    """
    assert cast(value) == expected


@pytest.mark.parametrize(
    "alpha,bravo,expected",
    [
        (cast(None), cast(None), Property(type="null", count=2)),
        (cast(True), cast(False), Property(type="boolean", count=2)),
        (
            cast(1),
            cast(1),
            DiscreteProperty(type="number", count=2, values={1: 2}),
        ),
        (
            cast(1),
            cast(2),
            DiscreteProperty(type="number", count=2, values={1: 1, 2: 1}),
        ),
        (cast(3.14), cast(1.221), Property(type="number", count=2)),
        (
            cast("hello"),
            cast("world"),
            DiscreteProperty(type="string", count=2, values={"hello": 1, "world": 1}),
        ),
        (
            cast("foo"),
            cast("foo"),
            DiscreteProperty(type="string", count=2, values={"foo": 2}),
        ),
        (
            DiscreteProperty(type="string", count=21, values={"red": 13, "green": 8}),
            DiscreteProperty(type="string", count=6, values={"red": 2, "blue": 4}),
            DiscreteProperty(
                type="string",
                count=27,
                values={"red": 15, "green": 8, "blue": 4},
            ),
        ),
        (
            cast({"size": 14, "color": "red"}),
            cast({"size": 14, "color": "blue"}),
            ObjectProperty(
                type="object",
                properties={
                    "size": DiscreteProperty(type="number", count=2, values={14: 2}),
                    "color": DiscreteProperty(
                        type="string", count=2, values={"red": 1, "blue": 1}
                    ),
                },
                count=2,
            ),
        ),
        (
            cast({"size": 14, "color": "red", "tags": ["foo", "bar"]}),
            cast({"size": 14, "color": "blue", "name": "Shirt"}),
            ObjectProperty(
                type="object",
                properties={
                    "name": DiscreteProperty(
                        type="string", count=1, unique=1, values={"Shirt": 1}
                    ),
                    "size": DiscreteProperty(
                        type="number", count=2, unique=1, values={14: 2}
                    ),
                    "color": DiscreteProperty(
                        type="string", count=2, unique=2, values={"red": 1, "blue": 1}
                    ),
                    "tags": ArrayProperty(
                        items=DiscreteProperty(
                            type="string",
                            count=2,
                            unique=2,
                            values={"foo": 1, "bar": 1},
                        ),
                        count=1,
                    ),
                },
                count=2,
            ),
        ),
        (
            cast(["red", "green", "blue"]),
            cast(["red", "green", "yellow"]),
            ArrayProperty(
                items=DiscreteProperty(
                    type="string",
                    count=6,
                    unique=5,
                    values={"red": 2, "green": 2, "blue": 1, "yellow": 1},
                ),
                count=2,
            ),
        ),
        (
            cast(3.14),
            AmbiguousProperty(
                types=[
                    Property(type="number", count=1),
                    Property(type="boolean", count=1),
                ],
                count=2,
            ),
            AmbiguousProperty(
                types=[
                    Property(type="boolean", count=1),
                    Property(type="number", count=2),
                ],
                count=3,
            ),
        ),
        (
            cast(3.14),
            AmbiguousProperty(
                types=[
                    Property(type="null", count=1),
                    Property(type="boolean", count=1),
                ],
                count=2,
            ),
            AmbiguousProperty(
                types=[
                    Property(type="boolean", count=1),
                    Property(type="null", count=1),
                    Property(type="number", count=1),
                ],
                count=3,
            ),
        ),
        (
            AmbiguousProperty(
                types=[
                    Property(type="null", count=1),
                    Property(type="boolean", count=1),
                ],
                count=2,
            ),
            AmbiguousProperty(
                types=[
                    Property(type="null", count=2),
                    Property(type="boolean", count=1),
                ],
                count=2,
            ),
            AmbiguousProperty(
                types=[
                    Property(type="boolean", count=2),
                    Property(type="null", count=3),
                ],
                count=5,
            )
        ),
        (
            AmbiguousProperty(
                types=[
                    Property(type="null", count=1),
                    Property(type="text", count=8),
                ],
                count=9,
            ),
            AmbiguousProperty(
                types=[
                    Property(type="null", count=3),
                    Property(type="boolean", count=4),
                ],
                count=7,
            ),
            AmbiguousProperty(
                types=[
                    Property(type="boolean", count=4),
                    Property(type="null", count=4),
                    Property(type="text", count=8),
                ],
                count=16,
            ),
        ),
    ],
)
def test_property_merge(alpha, bravo, expected):
    """
    Test merging properties.
    """
    assert alpha.merge(bravo) == expected


def test_discrete_values():
    """
    Assert discrete values must be a defaultdict or dict.
    """
    with pytest.raises(PropertyTypeError):
        DiscreteProperty(
            type="string",
            count=10,
            values=42,
        )


def test_no_nested_ambiguous():
    """
    Assert ambiguous types cannot contain other ambiguous types.
    """
    with pytest.raises(PropertyValueError):
        AmbiguousProperty(
            types=[
                Property(type="string", count=5),
                AmbiguousProperty(
                    types=[
                        Property(type="string", count=5),
                        Property(type="number", count=5),
                    ],
                    count=5,
                ),
            ],
            count=10,
        )

    with pytest.raises(PropertyValueError):
        prop = AmbiguousProperty(
            types=[
                Property(type="string", count=10),
            ],
            count=10,
        )

        MockAmbiguousProperty = namedtuple(
            "MockAmbiguousProperty", ["type", "types", "count"]
        )

        mock = MockAmbiguousProperty(
            type="ambiguous",
            types=[
                Property(type="string", count=5),
                AmbiguousProperty(types=[Property(type="number", count=5)], count=5),
            ],
            count=5,
        )

        prop.merge(mock)
