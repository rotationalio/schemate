"""
Utility to analyze the JSON schema of a document or a group of documents.
"""

from .types import Type
from .loaders import Loader
from .schemate import Profile, PropertyType, cast


class SchemaAnalysis(object):
    """
    Loads schemaless documents and analyzes the keys, their values, and their
    properties. Returns a schema profile of the documents that can be saved to disk.

    Parameters
    ----------
    loader : Loader
        A loader that provides the documents to be analyzed. The loader must
        implement the `__iter__` method to yield documents.
    """

    def __init__(self, loader: Loader):
        self._loader = loader
        self._result = None

    @property
    def result(self):
        return self._result

    def run(self):
        """
        Perform an analysis on the documents provided by the loader.
        """
        self._result = Profile(schema=None)
        for document in self._loader:
            self.analyze(document)

        self._result.schema.truncate()
        self._result.ambiguous = self.ambiguous(self._result.schema)

    def analyze(self, document):
        # Count the number of documents in the dataset
        self._result.documents += 1

        # Update the schema
        if self._result.schema is None:
            self._result.schema = cast(document)
        else:
            self._result.schema.merge(cast(document))

    def ambiguous(self, property: PropertyType) -> int:
        if property.type == Type.AMBIGUOUS:
            return 1 + sum(self.ambiguous(p) for p in property.types)
        elif property.type == Type.OBJECT:
            return sum(self.ambiguous(p) for p in property.properties.values())
        elif property.type == Type.ARRAY:
            return self.ambiguous(property.items)
        else:
            return 0
