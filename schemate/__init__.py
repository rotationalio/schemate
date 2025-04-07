"""
Analyzes NoSQL or JSON documents to try to infer a schema or general properties.
"""

##########################################################################
## Module Info
##########################################################################

# Import the version number at the top level
from .version import get_version, __version_info__

# Ensure that logging is configured at import time
from .logging import setup_logging
setup_logging()


##########################################################################
## Package Version
##########################################################################

__version__ = get_version(short=True)
