"""
Configure an analysis or schema generation job.
"""

import os
import abc
import copy
import json
import yaml
import inspect

from typing import Any
from collections.abc import Mapping

from .exceptions import ConfigLoadError, InvalidConfiguration


class BaseConfig(Mapping):
    """
    Base configuration object and ABC to define configuration handling.
    """

    @classmethod
    @abc.abstractmethod
    def DEFAULTS(cls) -> dict:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def REQUIRED(cls) -> list:
        raise NotImplementedError

    def __init__(self, data=None):
        self._config = copy.deepcopy(self.DEFAULTS)
        for key, value in self._config.items():
            if inspect.isclass(value):
                self._config[key] = value()

        if data:
            self.update(data)
        self.validate()

    def update(self, conf: dict):
        """
        Update the configuration object with new values.
        NOTE: this is the only way to mutate the configuration object.
        """
        for key, value in conf.items():
            if key in self._config:
                orig = self[key]
                if isinstance(orig, dict):
                    orig.update(value)
                elif hasattr(orig, "update"):
                    orig.update(value)
                else:
                    self._config[key] = value
            else:
                self._config[key] = value

    def validate(self):
        """
        Check that any required configuration is present.
        """
        for key in self.REQUIRED:
            if key not in self or not self[key]:
                raise InvalidConfiguration(f"missing required configuration: {key}")

            if hasattr(self[key], "validate"):
                self[key].validate()

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __iter__(self):
        return iter(self._config)

    def __len__(self) -> int:
        return len(self._config)


class LoaderConfig(BaseConfig):

    DEFAULTS = {"type": None}
    REQUIRED = ["type"]
    TYPES = {
        "glob": "schemate.loaders.GlobLoader",
        "mongo": "schemate.loaders.MongoDBLoader",
        "mongodb": "schemate.loaders.MongoDBLoader",
        "directory": "schemate.loaders.DirectoryLoader",
        "dir": "schemate.loaders.DirectoryLoader",
        "jsonlines": "schemate.loaders.JSONLinesLoader",
        "jsonl": "schemate.loaders.JSONLinesLoader",
        "files": "schemate.loaders.FilesLoader",
    }

    def validate(self):
        super(LoaderConfig, self).validate()
        loader = self["type"].lower().strip()
        if loader not in self.TYPES:
            raise InvalidConfiguration(
                f"invalid loader type: {loader}"
            )


class AnalysisConfig(BaseConfig):

    DEFAULTS = {"loader": LoaderConfig}
    REQUIRED = ["loaders"]


class Config(BaseConfig):

    DEFAULTS = {
        "analyze": AnalysisConfig,
    }

    REQUIRED = [
        "analyze",
    ]

    @classmethod
    def load(cls, path: str) -> "Config":
        """
        Load a configuration file.
        """
        loader = None
        _, ext = os.path.splitext(os.path.basename(path))

        if ext == ".json":
            loader = json.load
        elif ext == ".yaml" or ext == ".yml":
            loader = yaml.safe_load
        else:
            raise ConfigLoadError(
                f"unsupported config file type: {ext}: supported types are .json and .yaml"
            )

        try:
            with open(path, "r") as f:
                data = loader(f)
                return cls(data)
        except FileNotFoundError as e:
            raise ConfigLoadError(f"config file not found: {path}") from e
        except Exception as e:
            raise ConfigLoadError("failed to load config file") from e
