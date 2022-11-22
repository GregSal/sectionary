import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from sections import is_empty

# Objects to be tested and the expected test results.
# Non working test objects are commented out.

#%%
class TestEmptyIdentifierFunction(unittest.TestCase):

    def setUp(self):
        self.isempty_tests_objects = [
            (None, True),
            ('', True),
            ([], True),
            ({}, True),
            # ([''], True),  #[''] has length of 1, so reports is not empty.
            (pd.DataFrame(), True),
            (pd.Series(dtype=object), True),
            (np.array([]), True),
            # np.array has non-zero length, so reports is not empty.
            # (np.full((2, 3), np.nan, dtype=float), True),
            (0, False),
            (' ', False),
            ([' '], False),
            ({None,0}, False),
            (pd.Series([0]), False),
            (pd.DataFrame([{0:0}, {None:1}], index=range(2), columns=range(3)), False),
            (np.array([[0,np.nan],[np.nan, np.nan]]), False),
            (np.full((2, 3), 0, dtype=float), False),
            (np.empty((2, 3), dtype=object), False)
            ]

    def test_empty_objects(self):
        for test_set in self.isempty_tests_objects:
            obj, expected = test_set
            with self.subTest(object=obj):
                result = is_empty(obj)
                self.assertEqual(result, expected)



if __name__ == '__main__':
    unittest.main()
