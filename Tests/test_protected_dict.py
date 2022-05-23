import unittest
from pathlib import Path

from sections import ProtectedDict


#%%
class TestProtectedDict(unittest.TestCase):
    @staticmethod
    def kwarg_func(**kwargs):
        return kwargs

    def test_dict_create(self):
        pr_d = ProtectedDict(a=1, b=2, c=3)
        self.assertDictEqual(pr_d, {'a': 1, 'b': 2, 'c': 3})

    def test_dict_create_with_protection(self):
        pr_d = ProtectedDict(a=1, b=2, c=3, protected_items=['a'])
        self.assertDictEqual(pr_d, {'a': 1, 'b': 2, 'c': 3})

    def test_dict_update_item(self):
        pr_d = ProtectedDict(a=1, b=2, c=3, protected_items=['a'])
        pr_d.update(b=4)
        self.assertDictEqual(pr_d, {'a': 1, 'b': 4, 'c': 3})

    def test_dict_update_dict(self):
        pr_d = ProtectedDict(a=1, b=2, c=3, protected_items=['a'])
        new_dict = {'b': 4, 'c': 5}
        pr_d.update(new_dict)
        self.assertDictEqual(pr_d, {'a': 1, 'b': 4, 'c': 5})

    def test_dict_dont_update(self):
        pr_d = ProtectedDict(a=1, b=2, c=3, protected_items=['a'])
        new_dict = {'a': 9, 'b': 4, 'c': 5}
        pr_d.update(new_dict)
        self.assertDictEqual(pr_d, {'a': 1, 'b': 4, 'c': 5})

    def test_dict_kwargs(self):
        pr_d = ProtectedDict(a=1, b=2, c=3, protected_items=['a'])
        test_dict = self.kwarg_func(**pr_d)
        self.assertDictEqual(test_dict, {'a': 1, 'b': 2, 'c': 3})

if __name__ == '__main__':
    unittest.main()
