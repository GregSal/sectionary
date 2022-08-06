import unittest
import random

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorValueError
from buffered_iterator import BufferOverflowWarning

import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Test Buffered Iterator')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)


#%% Test Text
TEST_LINES = '''Line 0
Second Line
Third Line
Fourth Line
Fifth Line
~Line 6
Line 7
Line 8
Line 9
Line 10
Line 11
Line 12
'''
# from pprint import pprint
# pprint(TEST_LINES.splitlines())
#for i,l in enumerate(TEST_LINES.splitlines()):
#    print(f'{i}\t{l}')



#%%  Prescribed dose parse tests
class TestBufferedIterator(unittest.TestCase):
    def setUp(self):
        self.test_lines = TEST_LINES.splitlines()
        self.buffer_size = 5
        self.test_iter = BufferedIterator(self.test_lines,
                                         buffer_size=self.buffer_size)

    def test_backup(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        self.test_iter.step_back = 2
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_backup_error(self):
        # Step through 1st line
        yielded_lines = list()
        for i in range(1):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Try to Backup 2 lines
        with self.assertRaises(ValueError):
            self.test_iter.step_back = 2

    def test_backup_beyond_buffer_error(self):
        #  Step through more lines than buffer size
        yielded_lines = list()
        for i in range(self.buffer_size+1):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Try to Backup 2 lines
        with self.assertRaises(ValueError):
            self.test_iter.step_back = self.buffer_size+1

    def test_backup_method(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        self.test_iter.backup(2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-2])

    def test_look_back(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Backup 2 lines
        previous_line = self.test_iter.look_back(2)
        self.assertEqual(previous_line, yielded_lines[-2])
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3])

    def test_look_ahead(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Look 2 lines ahead
        future_line = self.test_iter.look_ahead(2)
        # Step through 2 more lines
        for i in range(2):
            yielded_lines.append(self.test_iter.__next__())
        self.assertEqual(future_line, yielded_lines[-1])

    def test_skip(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        previous_line = yielded_lines[-1]
        #Skip 3 lines ahead
        self.test_iter.skip(3)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3+3])
        #Backup 2 lines
        self.test_iter.backup(2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, previous_line)


    def test_advance(self):
        # Step through 1st 3 lines
        yielded_lines = list()
        for i in range(3):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        previous_line = yielded_lines[-1]
        #Advance 3 lines ahead
        self.test_iter.advance(3)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, self.test_lines[3+3])
        #Backup 3+2 lines
        self.test_iter.backup(3+2)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, previous_line)

    def test_max_backup(self):
        # Advance to fill the buffer
        yielded_lines = list()
        for i in range(self.buffer_size):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        #Backup the entire buffer
        self.test_iter.backup(self.buffer_size)
        next_line = self.test_iter.__next__()
        self.assertEqual(next_line, yielded_lines[-self.buffer_size])

    def test_source_overun(self):
        # Advance to fill the buffer
        yielded_lines = list()
        num_items = len(self.test_lines)
        with self.assertRaises(StopIteration):
            for i in range(num_items+1):  # pylint: disable=unused-variable
                yielded_lines.append(self.test_iter.__next__())

    def test_advance_overun(self):
        # Advance to fill the buffer
        yielded_lines = list()
        num_items = len(self.test_lines)
        for i in range(num_items):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        with self.assertRaises(BufferOverflowWarning):
            self.test_iter.advance(1)

    def test_look_back_overun(self):
        # Advance to fill the buffer
        yielded_lines = list()
        for i in range(1):  # pylint: disable=unused-variable
            yielded_lines.append(self.test_iter.__next__())
        with self.assertRaises(BufferedIteratorValueError):
            previous_line = self.test_iter.look_back(2)  # pylint: disable=unused-variable

class TestBufferedIteratorItemCount(unittest.TestCase):
    def setUp(self):
        self.buffer_size = 5
        self.num_items = 12
        self.str_source = BufferedIterator(
            (str(i) for i in range(self.num_items)),
            buffer_size=self.buffer_size
            )
        self.int_source = BufferedIterator(
            (i for i in range(self.num_items)),
            buffer_size=self.buffer_size
            )

    def test_initial_count_values(self):
        '''Before iteration starts BufferedIterator.item_count=0.
        '''
        self.assertEqual(self.str_source._item_count, 0)
        self.assertEqual(self.str_source.item_count, 0)

    def test_count_value_tracking(self):
        '''BufferedIterator.item_count should be one greater than the source
        item index for all items.
        '''
        for i in self.int_source:
            with self.subTest(i=i):
                self.assertEqual(i+1, self.int_source.item_count)

    def test_post_iteration_count_value(self):
        '''After iteration completes BufferedIterator.item_count should be the
        total number of items in the source.
        '''
        [i for i in self.int_source]
        self.assertEqual(self.num_items, self.int_source.item_count)

    def test_backup_count(self):
        '''When backup is called on a BufferedIterator iterator,
        BufferedIterator.item_count should decrease by the corresponding amount.
        '''
        fwd = random.randint(2, self.num_items-1)
        back = random.randint(1, min(fwd-1, self.buffer_size))
        print(f'Moving forward {fwd} steps; backing up {back} steps')
        for i in range(fwd):
            next(self.str_source)
        self.str_source.backup(back)
        self.assertEqual(fwd-back, self.str_source.item_count)
        self.assertEqual(int(self.str_source.previous_items[-1]),
                         self.str_source.item_count-1)

    def test_advance_count(self):
        '''When advance is called on a BufferedIterator iterator,
        BufferedIterator.item_count should increase by the corresponding amount.
        '''
        fwd = random.randint(0, self.num_items-2)
        adv = random.randint(1, min(self.num_items-fwd, self.buffer_size))
        print(f'Moving forward {fwd} steps; advancing {adv} more steps')
        for i in range(fwd):
            next(self.int_source)
        self.int_source.advance(adv)
        self.assertEqual(fwd+adv, self.int_source.item_count)
        self.assertEqual(self.int_source.previous_items[-1],
                         self.int_source.item_count-1)

class TestBufferedIterator_goto_item(unittest.TestCase):
    def setUp(self):
        self.buffer_size = 5
        self.num_items = 12
        self.str_source = BufferedIterator(
            (str(i) for i in range(self.num_items)),
            buffer_size=self.buffer_size
            )
        self.int_source = BufferedIterator(
            (i for i in range(self.num_items)),
            buffer_size=self.buffer_size
            )

    def test_goto_forward(self):
        '''BufferedIterator.goto_item(n) should make a call to __next__()
        return the n_th item in the sequence.
        '''
        fwd = random.randint(1, self.num_items-2)
        max_adv = fwd + min(self.num_items-fwd+1, self.buffer_size)
        item_choices = [i for i in range(fwd+1, max_adv)]
        target_item = random.choice(item_choices)
        logger.debug(f'Moving forward {fwd} steps; going to item {target_item}')
        for i in range(fwd):
            next(self.int_source)
        self.int_source.goto_item(target_item)
        self.assertEqual(target_item, self.int_source.item_count)
        self.assertEqual(next(self.int_source), self.int_source.item_count-1)

    def test_goto_backwards(self):
        '''BufferedIterator.goto_item(n) should make a call to __next__()
        return the n_th item in the sequence.  When moving backwards, n is
        limited to item_count - buffer_size (the items in previous_items).
        '''
        fwd = random.randint(2, self.num_items-1)
        item_idx = fwd - 1
        buffer_len = min(self.buffer_size, fwd)
        max_back = item_idx - buffer_len + 1
        item_choices = [i for i in range(item_idx, max_back, -1)]
        target_item = random.choice(item_choices)
        logger.debug(f'Moving forward {fwd} steps; going to item {target_item}')
        for i in range(fwd):
            next(self.int_source)
        self.int_source.goto_item(target_item)
        self.assertEqual(target_item, self.int_source.item_count)
        self.assertEqual(next(self.int_source), self.int_source.item_count-1)

    def test_goto_beginning(self):
        '''BufferedIterator.goto_item(0) should restart the iterator.
        '''
        # In order to move to the beginning the current location must be less
        # than the buffer size.
        fwd = random.randint(1, min(self.buffer_size, self.num_items-1))
        logger.debug(f'Moving forward {fwd} steps; going to item 0')
        for i in range(fwd):
            next(self.int_source)
        self.int_source.goto_item(0)
        self.assertEqual(self.str_source.item_count, 0)

class TestBufferedIterator_goto_item_Errors(unittest.TestCase):
    '''Test that appropriate error messages are raised with illegal goto_item
    calls.
    '''
    def setUp(self):
        self.buffer_size = 2
        self.num_items = 8
        self.str_source = BufferedIterator(
            (str(i) for i in range(self.num_items)),
            buffer_size=self.buffer_size
            )
        self.int_source = BufferedIterator(
            (i for i in range(self.num_items)),
            buffer_size=self.buffer_size
            )

    def test_goto_with_unstarted_iterator(self):
        '''BufferedIterator.goto_item(n) cannot execute when iterator is at the
        beginning.
        '''
        with self.assertRaises(BufferedIteratorValueError):
            self.str_source.goto_item(1)

    def test_goto_backwards_past_buffer_limit(self):
        '''BufferedIterator.goto_item(n) cannot reach items that have been
        dropped from the previous_items buffer.
        '''
        # Move forward until the beginning of the sequence has been lost from
        # the buffer.
        fwd = random.randint(self.str_source.buffer_size+1, self.num_items-1)
        for i in range(fwd):
            next(self.str_source)
        with self.assertRaises(BufferedIteratorValueError):
            self.str_source.goto_item(0)

    def test_goto_forwards_past_buffer_limit(self):
        '''BufferedIterator.goto_item(n) raises an error if the number of steps
        required to reach 'n' is larger than the buffer size.  (The current item
        will be lost.)
        '''
        # Do not move forward beyond the point where than there are less
        # remaining  source items than the size of the buffer.
        fwd_choices = [i for i in range(1, self.num_items-self.buffer_size-2)]
        fwd = random.choice(fwd_choices)
        min_adv = fwd + self.buffer_size + 1
        item_choices = [i for i in range(min_adv, self.num_items-2)]
        target_item = random.choice(item_choices)
        for i in range(fwd):
            next(self.str_source)
        with self.assertRaises(BufferedIteratorValueError):
            self.str_source.goto_item(target_item, buffer_overrun=False)

    def test_goto_forwards_past_buffer_limit_allowed(self):
        '''If `buffer_overrun=True`, `BufferedIterator.goto_item(n)` does not
        raise an error if the number of steps required to reach 'n' is larger
        than the buffer size.  (The current item will still be lost.)
        '''
        fwd_choices = [i for i in range(1, self.num_items-self.buffer_size-2)]
        fwd = random.choice(fwd_choices)
        min_adv = fwd + self.buffer_size + 1
        item_choices = [i for i in range(min_adv, self.num_items-1)]
        target_item = random.choice(item_choices)
        for i in range(fwd):
            next(self.int_source)
        self.int_source.goto_item(target_item, buffer_overrun=True)
        self.assertEqual(target_item, self.int_source.item_count)
        self.assertEqual(next(self.int_source), self.int_source.item_count-1)

    def test_goto_with_unstarted_iterator(self):
        '''BufferedIterator.goto_item(n) cannot go to an item number beyond
        the size of the sequence.
        '''
        # Move forward until the beginning of the sequence has been lost from
        # the buffer More than the size of the buffer.
        fwd = random.randint(1, self.num_items-2)
        for i in range(fwd):
            next(self.str_source)
        with self.assertRaises(BufferedIteratorValueError):
            self.str_source.goto_item(self.num_items+1)


class TestBufferedIteratorMinimumBufferSize(unittest.TestCase):
    '''BufferedIterator has a minimum buffer size of 1
    '''
    def test_minimum_buffer_size(self):
        '''Verify that BufferedIterator initialization raises an error if
        buffer_size < 1 is given.
        '''
        with self.assertRaises(BufferedIteratorValueError):
            test_iter = BufferedIterator(range(5), buffer_size=0)


if __name__ == '__main__':
    unittest.main()

# %%
