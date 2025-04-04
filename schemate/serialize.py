"""
Helpers for serializing and deserializing python types from JSON
"""

import json
import enum
import dataclasses


class Encoder(json.JSONEncoder):

    def default(self, o):
        if hasattr(o, "asdict") and callable(o.asdict):
            return o.asdict()

        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        if isinstance(o, enum.Enum):
            return o.value

        return super(Encoder, self).default(o)
