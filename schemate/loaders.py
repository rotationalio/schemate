"""
Data loaders for iterating through schemaless datasources
"""

import os
import glob
import json
import yaml

from pymongo import MongoClient
from collections.abc import Iterable, Sized
from .exceptions import UnsupportedLoader, LoaderError


class Loader(Iterable, Sized):
    """
    A loader class is an interator that reads schemaless datasources such as a MongoDB
    collection or a directory of files and yields Python dictionaries with the
    deserialized data from those sources. It may also provide other methods for
    connection management and filtering.
    """

    def count(self):
        """
        Returns the total number of documents being managed by the loader.
        """
        return len(self)


class FileLoader(Loader):
    """
    Loads documents from a single yaml, json, or jsonlines file based on the extension.
    If the file is yaml or json, it yields a single document (count=1). If it is a
    jsonlines file it yields one document per line (count=n).

    Parameters
    ----------
    path : str
        The path to the file to load. Its extension must be one of the supported types.
    """

    SUPPORTED_TYPES = {
        ".json", ".jsonlines", ".jsonl", ".yaml", ".yml"
    }

    @staticmethod
    def is_supported(path: str) -> bool:
        """
        Returns true if the extension of the specified path is one of the supported
        file types that can be loaded by this class.
        """
        return FileLoader.extension(path) in FileLoader.SUPPORTED_TYPES

    @staticmethod
    def extension(path: str) -> str:
        """
        Returns the normalized extension of the specified path.
        """
        return os.path.splitext(os.path.basename(path))[1].lower()

    def __init__(self, path: str):
        self._path = path
        self._ext = self.extension(path)
        self._count = None

        if self._ext not in self.SUPPORTED_TYPES:
            raise UnsupportedLoader(f"unsupported file type: {self._ext}")

    def __len__(self):
        if self._count is None:
            # In this case we haven't performed an iteration, so count manually.
            if self._ext in {".jsonlines", ".jsonl"}:
                self._count = sum(1 for _ in self.load_jsonlines())
            else:
                self._count = 1
        return self._count

    def __iter__(self):
        self._count = 0
        for document in self.load():
            self._count += 1
            yield document

    def load(self):
        """
        Uses the extension of the wrapped path to return the data in the file.
        """
        try:
            if self._ext == ".json":
                return self.load_json()
            elif self._ext in {".yaml", ".yml"}:
                return self.load_yaml()
            elif self._ext in {".jsonlines", ".jsonl"}:
                return self.load_jsonlines()
            else:
                raise UnsupportedLoader(f"unsupported file type: {self._ext}")
        except OSError as e:
            raise LoaderError(f"unable to open file: {self._path}") from e
        except FileNotFoundError as e:
            raise LoaderError(f"missing data file: {self._path}") from e

    def load_json(self) -> dict:
        """
        Loads the file as a single JSON document.
        """
        with open(self._path, "r") as f:
            return [json.load(f)]

    def load_yaml(self) -> dict:
        """
        Loads the file as a single YAML document.
        """
        with open(self._path, "r") as f:
            return [yaml.safe_load(f)]

    def load_jsonlines(self) -> Iterable[dict]:
        """
        Loads a jsonlines file where each line is a JSON document.
        """
        with open(self._path, "r") as f:
            for line in f:
                yield json.loads(line)


class MultiFileLoader(Loader):
    """
    Loads documents from a list of files. The files can be of any supported type by the
    FileLoader class. The loader will iterate through the files and yield documents from
    each file using the FileLoader.

    Parameters
    ----------
    paths : list[str]
        A list of paths to the files to load.

    ignore_unsupported : bool (default: True)
        If True, the paths will be filtered to exclude unsupported file types; otherwise
        an exception will be raised if any unsupported file types are found.
    """

    def __init__(self, paths: list[str], ignore_unsupported: bool = True):
        if ignore_unsupported:
            paths = [
                path for path in paths if FileLoader.is_supported(path)
            ]

        self._count = None
        self._loaders = [
            FileLoader(path) for path in paths
        ]

    def __len__(self):
        if self._count is None:
            self._count = sum(len(loader) for loader in self._loaders)
        return self._count

    def __iter__(self):
        self._count = 0
        for loader in self._loaders:
            for document in loader.load():
                self._count += 1
                yield document

    def filenames(self):
        for loader in self._loaders:
            yield loader._path


class DirectoryLoader(MultiFileLoader):
    """
    Loads all the documents in a directory and optionally all subdirectories. The
    directories must only contain documents of the supported types in the FileLoader
    class (otherwise those files will be ignored). This class also supports loading of
    multiple directories.

    Parameters
    ----------
    dirs : str | list[str]
        A directory path or a list of directory paths to load files from.

    recursive : bool (default: False)
        If True, the loader will recursively load all files in the directory and its
        subdirectories. Otherwise, it will only load files in the top-level directory.

    ignore_unsupported : bool (default: True)
        If True, the paths will be filtered to exclude unsupported file types; otherwise
        an exception will be raised if any unsupported file types are found.
    """

    def __init__(self, dirs: str | list[str], recursive: bool = False, ignore_unsupported: bool = True):
        paths = []
        if isinstance(dirs, str):
            dirs = [dirs]

        # Get all the files in the directories and subdirectories if recursive.
        for dir in dirs:
            for root, _, filenames in os.walk(dir):
                for filename in filenames:
                    paths.append(os.path.join(root, filename))
                if not recursive:
                    break

        super().__init__(paths, ignore_unsupported=ignore_unsupported)


class GLOBLoader(MultiFileLoader):
    """
    Loads all files that match the specified glob pattern(s).

    Parameters
    ----------
    patterns : str | list[str]
        A glob pattern or a list of glob patterns to load files from.

    ignore_unsupported : bool (default: True)
        If True, the paths will be filtered to exclude unsupported file types; otherwise
        an exception will be raised if any unsupported file types are found.
    """

    def __init__(self, patterns: str | list[str], ignore_unsupported: bool = True):
        paths = []
        if isinstance(patterns, str):
            patterns = [patterns]

        for pattern in patterns:
            paths.extend(glob.glob(pattern))

        super().__init__(paths, ignore_unsupported=ignore_unsupported)


class MongoDBLoader(Loader):
    """
    Loads documents from a collection (or collections) in a MongoDB database.

    Parameters
    ----------
    uri : str
        The MongoDB connection URI.

    db : str
        The name of the database to connect to. Note that if the db doesn't exist on
        the server, no documents will be returned.

    collections : str | list[str]
        The name of the collection(s) to load documents from. If a list is provided,
        documents from all specified collections will be loaded. Note that if the
        collection does not exist on the server, no documents will be returned.
    """

    def __init__(self, uri: str, db: str, collections: str | list[str]):
        self._client = MongoClient(uri)
        self._db = self._client[db]
        self._collections = []
        self._count = None

        # TODO: do we need to check if the collections and database exist first?
        if isinstance(collections, str):
            self._collections.append(self._db[collections])
        else:
            for collection in collections:
                self._collections.append(self._db[collection])

    def __len__(self):
        if self._count is None:
            self._count = sum(
                collection.count_documents({})
                for collection in self._collections
            )
        return self._count

    def __iter__(self):
        self._count = 0
        for collection in self._collections:
            for document in collection.find():
                self._count += 1
                yield document
