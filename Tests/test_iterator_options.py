''' Testing Subsection break issues.'''

# %% Imports
import unittest
from buffered_iterator import BufferedIterator
from sections import SectionBreak, Section

# %%
class TestIteratorOptions(unittest.TestCase):
    def setUp(self):
        self.test_text = [
            'Text to be ignored',
            'StartSection Name: A',
            'EndSection Name: A',
            'StartSection Name: B',
            'EndSection Name: B',
            'More text to be ignored',
            ]

        self.test_section = Section(
            start_section=SectionBreak('StartSection', break_offset='Before'),
            end_section=SectionBreak('EndSection', break_offset='After')
            )

    def test_regular_iterator(self):
        test_iter = iter(self.test_text)
        read_1 = self.test_section.read(test_iter)
        read_2 = self.test_section.read(test_iter)

        self.assertListEqual(
            read_1,
            ['StartSection Name: A', 'EndSection Name: A']
            )
        self.assertListEqual(read_2, [])

    def test_buffered_iterator(self):
        test_iter = BufferedIterator(self.test_text)
        read_1 = self.test_section.read(test_iter)
        read_2 = self.test_section.read(test_iter)
        read_3 = self.test_section.read(test_iter)

        self.assertListEqual(
            read_1,
            ['StartSection Name: A', 'EndSection Name: A']
            )
        self.assertListEqual(
            read_2,
            ['StartSection Name: B', 'EndSection Name: B']
            )
        self.assertListEqual(read_3, [])


if __name__ == '__main__':
    unittest.main()

# %%
