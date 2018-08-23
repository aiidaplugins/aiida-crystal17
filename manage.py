#import sys
import unittest
from aiida_crystal17.tests import get_backend
from aiida.utils.fixtures import TestRunner

tests = unittest.defaultTestLoader.discover('.')
result = TestRunner().run(tests, backend=get_backend())

# Note: On travis, this will not fail even if the tests fail.
# Uncomment the lines below, when aiida 0.12.2 is released to fix this.
#exit_code = int(not result.wasSuccessful())
#sys.exit(exit_code)
