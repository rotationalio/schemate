"""
Tests for the configuration module.
"""

import pytest

from schemate.config import BaseConfig
from schemate.exceptions import InvalidConfiguration


class MockConfig(BaseConfig):

    DEFAULTS = {
        "color": "red",
        "size": "large",
    }

    REQUIRED = ["color", "name"]


def test_config_base():
    """
    Test the base functionality of the config object.
    """
    with pytest.raises(InvalidConfiguration):
        _ = MockConfig()

    config = MockConfig({"name": "test", "color": "blue"})
    assert config["name"] == "test"
    assert config["color"] == "blue"
    assert config["size"] == "large"
