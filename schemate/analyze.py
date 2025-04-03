"""
Utility to analyze the JSON schema of a document or a group of documents.
"""

from .loaders import Loader
from .schemate import Profile


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

    def analyze(self, document):
        self._result.documents += 1
        pass
