"""
Helpers for serializing and deserializing python types from JSON
"""

import json
import dataclasses


class Encoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        return super(Encoder, self).default(o)
