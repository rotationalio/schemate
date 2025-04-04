"""
Test the schemaless types module.
"""

import pytest

from schemate.types import *


@pytest.mark.parametrize(
    "sb,expected",
    [
        ("", False),
        ("aGVsbG8gd29ybGQ=", True),
        ("gqSb/4Kkm6d+pJvLgqSb/4Kkl/+CpJf/fqSbl36kmJ9+pJgA", True),
        ("not base 64", False),
        ("TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseS4", False),
        ("TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseS4=", True),
        ("TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseSAt", True),
        ("TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseSAtLQ=", False),
        ("TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseSAtLQ", False),
        ("TG9uZyBiYXNlNjQgZW5jb2RlZCBzdHJpbmcsIGhvcGVmdWxseSAtLQ==", True),
        (None, False),
        (42, False)
    ],
)
def test_is_base64(sb, expected):
    """
    Test the is_base64 function.
    """
    assert is_base64(sb) is expected
