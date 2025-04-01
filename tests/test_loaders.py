"""
Test the document loaders.
"""

import pytest

from schemate.loaders import *


def test_loader_base_class():

    class MockLoader(Loader):

        def __iter__(self):
            yield {"color": "red", "size": "large"}
            yield {"color": "blue", "size": "small"}
            yield {"color": "red"}

        def __len__(self):
            return 3

    loader = MockLoader()
    assert loader.count() == 3


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/path/to/file.json", True),
        ("/path/to/file.JSON", True),
        ("/path/to/file.Json", True),
        ("file.json", True),
        ("/path/to/file.jsonl", True),
        ("/path/to/file.jsonlines", True),
        ("/path/to/file.yaml", True),
        ("/path/to/file.yml", True),
        ("/path/to/file.txt", False),
        ("file.txt", False),
        ("file", False),
        ("", False),
    ],
)
def test_file_loader_is_supported(path, expected):
    """
    Test the file loader's is_supported method.
    """
    assert FileLoader.is_supported(path) is expected
