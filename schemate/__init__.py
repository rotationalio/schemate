"""
Analyzes NoSQL or JSON documents to try to infer a schema or general properties.
"""

##########################################################################
## Module Info
##########################################################################

# Import the version number at the top level
from .version import get_version, __version_info__


##########################################################################
## Package Version
##########################################################################

__version__ = get_version(short=True)
