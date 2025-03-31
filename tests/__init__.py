"""
Testing for the schemate package.
"""

##########################################################################
## Imports
##########################################################################

import unittest


##########################################################################
## Test Cases
##########################################################################


class InitializationTest(unittest.TestCase):

    def test_initialization(self):
        """
        Tests a simple world fact by asserting that 10*10 is 100.
        """
        self.assertEqual(10*10, 100)

    def test_import(self):
        """
        Can import confire
        """
        try:
            import schemate
        except ImportError:
            self.fail("Unable to import the schemate module!")
