'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
from __future__ import annotations
from copy import copy
from collections import deque

from typing import Sequence, TypeVar, Union
import logging
SourceItem = TypeVar('SourceItem')

#%% Logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logger = logging.getLogger('Buffered Iterator')
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)

#%% Exceptions
class BufferedIteratorWarnings(UserWarning):
    '''Base Warning class for BufferedIterator.'''

class BufferedIteratorException(Exception):
    '''Base Exception class for BufferedIterator.'''

class BufferedIteratorValueError(BufferedIteratorException, ValueError):
    '''Base Exception class for BufferedIterator.'''

class BufferedIteratorEOF(BufferedIteratorException, StopIteration):
    '''Raised when the source supplied to BufferedIterator is exhausted.
    '''

class BufferOverflowWarning(BufferedIteratorWarnings):
    '''Raised when BufferedIterator peak will cause un-yielded
        lines to be dropped.
    '''


#%% Classes
class BufferedIterator():
    '''Iterate through sequence allowing for backup and look ahead.

    BufferedIterator is an iterator tool for any type of Sequence object,
    providing a means to step in both directions.  It's primary feature are two
    queues: previous_items and future_items, storing previous visited items.
    It also contains an internal enumerator, which can be used as an index to
    move to a particular spot in the sequence.

    Attributes:
        previous_items (deque): The last n items consumed by the iterator,
            where n is the iterator's buffer_size attribute. A next() call will
            append the item returned to the previous_items queue, and if full,
            drop an item from the other end of the queue.  The backup() and
            rewind() calls pull items from this queue.
        future_items (deque): Contains items consumed by the base iterator, but
            before the current pointer.  Populated by calls such as
            look_ahead() and advance()
        buffer_size (int): The size of the previous_items and future_items
            queues. buffer_size can only be set at instance creation.
        item_count (int): A read-only attribute indicating the number of items
            used (position) in the iterator.
            To match normal python indexing, item_count = 0 represents the
            beginning of the sequence. (i.e. A next() call will return the
            first item in the sequence).
        source_gen (Iterator): The base iterator created at object
            initialization from the supplied Sequence.  Generally there should
            be no reason to access this directly.
        status (str): Possible states are:
            CREATED: Defined, but not started.
            ACTIVE: Currently open with more items in the underlying sequence.
            CLOSED: All items in the underlying sequence are exhausted.

    Methods:
        next() and iter(): BufferedIterator supports the standard next()
            and iter() methods.
        backup(steps: int = 1): Move the iterator pointer back the given number
            of steps.
        skip(steps: int = 1): Ignore the given number of items in the source.
            The items  in between cannot be retrieved with backup or look_back.
        advance(steps: int = 1, buffer_overrun=False):  Move the given number
            of items forward through in source.  The items passed over can be
            retrieved with backup or look_back.
        look_back(steps: int = 1)->SourceItem: Return the item the given number
            of steps back, but do not move the position in the source.
        look_ahead(steps: int = 1)->SourceItem: Return the item the given number
            of steps ahead, but do not move the position in the source.
        goto_item(item_num: int, buffer_overrun=False): Move the position in the
            source to the given item number.  Do not return the items in
            between. The items passed over can be retrieved with backup() or
            look_back().
    '''
    def __init__(self, source: Sequence[SourceItem], buffer_size=5):
        '''Create a new BufferedIterator, linking it with the supplied Sequence
            and initialize the forward and reverse buffers.

        Args:
            source (Sequence[SourceItem]): The sequence to be iterated over.
            buffer_size (int, optional): The size of the forward and reverse
                buffers. the size of these buffers dictate how far forward and
                backwards it is possible to shift the pointer. Defaults to 5.

        Raises:
            BufferedIteratorValueError: Raised if the supplied buffer_size is
                less than 1.
        '''
        if buffer_size < 1:
            raise BufferedIteratorValueError('Buffer size must be 1 or greater')
        self._buffer_size = buffer_size
        self.source_gen = iter(source)
        self.previous_items = deque(maxlen=buffer_size)
        self.future_items = deque(maxlen=buffer_size)
        self._step_back = 0
        self._item_count = 0
        self._status = 'Created'
        return

    @property
    def status(self):
        if self._item_count == 0:
            return 'CREATED'
        if len(self.future_items) > 0:
            return 'ACTIVE'
        if 'Completed' in self._status:
            return 'CLOSED'
        return 'ACTIVE'

    @property
    def buffer_size(self)->int:
        return self._buffer_size

    @property
    def item_count(self) -> int:
        '''Number of items used in iterator.

        Returns: int: Counting starts with 1.
        '''
        return int(self._item_count)

    @property
    def step_back(self) -> int:
        '''The number of steps backwards to move the iterator pointer.'''
        return self._step_back

    @step_back.setter
    def step_back(self, steps: int):
        '''Move the iterator pointer back the given number of steps.

        Compares the requested "steps" back against the size of the
            "previous_items" queue. If the queue has enough items, sets the
            "step_back" property to "steps". Otherwise raises
            "BufferedIteratorValueError" exception.  Steps must be a positive
            integer. Negative values for steps will raise the
            "BufferedIteratorValueError" exception. A value of zero will be
            ignored.  Float values will be truncated to integers.

        Args:
            steps (int): The given number of steps to set for the "step_back"
               property.
        Raises:
            BufferedIteratorValueError: Indicates an invalid "steps" value.
                Either a larger value than the number of items in the
                "previous_items" queue, or a negative value.
        Returns:
            None.
        '''
        logger.debug(f'Have {len(self.previous_items)} Previous Items')
        logger.debug(f'Need {steps} Steps back')
        steps = self.check_steps(steps)
        self._step_back = steps
        self.rewind()

    def get_next_item(self) -> SourceItem:
        '''Get the next item from the source. Called by skip() and advance().
        Usually not called directly.

        If there are items in the "future_items" queue, return the next item
            from the queue.  Otherwise read from the "source_gen".  If reading
            from  "source_gen" returns a "StopIteration" or "RuntimeError",
            raise "BufferedIteratorEOF", with information passed from the
            original error.

        Raises:
            BufferedIteratorEOF: Indicates end of the source file or stream.
                Raised when the source generator returns a "StopIteration" or
                "RuntimeError".  Note: When a Generator functions raises a
                "StopIteration", Python converts it to a "RuntimeError".

        Returns:
            SourceItem: The next item from the source.
        '''
        # Check the "future_items" queue for items.
        if len(self.future_items) > 0:
            # Get the next item from the queued items
            next_item = self.future_items.popleft()
            self._item_count += 1
            logger.debug(f'Getting item: {next_item}\t from future_items')
        else:
            # Get the next item from the source iterator
            try:
                # Read from the iterator source
                next_item = self.source_gen.__next__()
            except (StopIteration, RuntimeError) as eof:
                # Treat "StopIteration" or "RuntimeError" exceptions as
                # End-of-File indicators.
                self._status = 'Completed'
                raise BufferedIteratorEOF from eof
            else:
                self._item_count += 1
                self._status = 'Started'
                logger.debug(f'Getting item: {next_item}\t from source')
        return next_item

    def __next__(self) -> SourceItem:
        '''Return the next item in a sequence allowing for retracing steps.

        Calls get_next_item checking for "BufferedIteratorEOF" and
           propagating the exception.  As each item is obtained from the source
           it is added to the "previous_items" queue to allow for moving
           backwards through the source.

        Raises:
            BufferedIteratorEOF:  Indicates that the iterator has closed.

        Returns:
            SourceItem: The next item from the source.
        '''
        try:
            next_line = self.get_next_item()
        except BufferedIteratorEOF as eof:
            raise eof
        self.previous_items.append(next_line)
        return next_line

    def __iter__(self) -> SourceItem:
        '''Step through a sequence allowing for retracing steps.

        Calls __next__ until "BufferedIteratorEOF" is raised.  Does not
           propagate the exception.

        Yields:
            SourceItem: The next item from the source.
        '''
        while True:
            try:
                next_line = self.__next__()
            except BufferedIteratorEOF:
                break
            else:
                yield next_line
        return

    def check_steps(self, steps: int, backwards=True, skip=False)->int:
        '''Check the steps value.  This method is usually not called directly.

        Convert number-like "steps" to int.  If conversion fails, raise the
            "BufferedIteratorValueError" exception.
        Verify that "steps" is a positive integer; for negative values
            raise the "BufferedIteratorValueError" exception.
        If "backwards", verify that "steps" is less than the size of the
            "previous_items" queue; if not, raise "BufferedIteratorValueError"
            exception.

        Args:
            steps (int): The given number of steps to shift the iterator
                pointer.
            backwards (bool, optional): If True steps is number of iterator
                steps to move backwards, otherwise steps is number of iterator
                steps to move forwards. Defaults to True.
            skip (bool, optional): If True do not check if items will be lost
            due to a buffer overflow. Defaults to False.
        Raises:
            BufferedIteratorValueError: Indicates an invalid "steps" value.
                "steps" can be invalid due to an incorrect type, a negative
                value or a value that is too large.
        Returns:
            None.
        '''
        # Force int conversion
        try:
            steps = int(steps)  # Force steps to be an integer
        except ValueError as err:
            raise BufferedIteratorValueError(
                f'steps must be a positive integer. Got: {steps}') from err
        # Check for negative steps values
        if steps < 0:
            raise BufferedIteratorValueError(
                f'steps must be a positive integer. Got: {steps}')
        if backwards:
            # Check for available previous items
            if len(self.previous_items) < steps:
                msg = (f"Can't step back {steps} items.\n\t"
                       f"only have {len(self.previous_items)} previous items "
                        "available.")
                raise BufferedIteratorValueError(msg)
        elif not skip:
            # Check that steps < buffer_size
            if steps > self.buffer_size:
                raise BufferedIteratorValueError(
                    f'The value of steps ({steps}) exceeds the buffer_size. '
                    'Will not be able to retain all skipped items.')
        return steps

    def rewind(self):
        '''
        Move the iterator pointer back the number of steps set in the
        "step_back" property.  Usually not called directly().

        The appropriate number of items in the "previous_items" queue are
           moved to the "future_items" queue and the "step_back" property is
           reset to 0. Called by backup()
        Returns:
            None.
        '''
        for step in range(self._step_back): # pylint: disable=unused-variable
            self._step_back -= 1
            self._item_count -= 1
            if len(self.previous_items) > 0:
                self.future_items.appendleft(self.previous_items.pop())
        self._step_back = 0

    def backup(self, steps: int = 1):
        '''Move the iterator pointer back the given number of steps.

        Sets the "step_back" property and then calls the "rewind" method.

         Args:
            steps (int, optional): The number of steps to move the iterator
            pointer backwards in the source. Defaults to 1.
        Returns:
            None.
       '''
        self.step_back = steps
        self.rewind()

    def skip(self, steps: int = 1):
        '''Ignore the next "steps" number of items in the source.

        Move the iterator pointer forward the given number of steps
           dropping the items in between.  The items dropped cannot be
           retrieved with backup or look_back.

        Args:
            steps (int, optional): The number of items to skip in the in the
                source.  A value of zero will be ignored.  Float values will
                be truncated to integers. Defaults to 1
        Raises:
            BufferedIteratorValueError: Raised if "steps" cannot be converted
                to an integer or is less than 0.
        Returns:
            None.
        '''
        steps = self.check_steps(steps, backwards=False, skip=True)
        for step in range(steps): # pylint: disable=unused-variable
            self.get_next_item()

    def advance(self, steps: int = 1, buffer_overrun=False):
        '''Move "steps" forward through the items in source.

        Move the iterator pointer forward the given number of steps
           storing the items in between as if they had been returned.  The
           items passed over can be retrieved with backup or look_back.

        Args:
            steps (int, optional): The number of items to advance in the in
                the source.  A value of zero will be ignored.  Float values
                will be truncated to integers. Defaults to 1
            buffer_overrun (bool, optional): If True do not check whether
                items will be lost from the buffer.

        Raises:
            BufferedIteratorValueError: Raised if "steps" cannot be converted
                to an integer or is less than 0.
        Returns:
            None.
        '''
        steps = self.check_steps(steps, backwards=False, skip=buffer_overrun)
        for step in range(steps):  # pylint: disable=unused-variable
            try:
                next_item = self.get_next_item()
            except BufferedIteratorEOF as eof:
                raise BufferOverflowWarning(
                    f'advance({steps}) exceeds the remaining items available '
                    'in source.  Advancing to the end of source.') from eof
            else:
                self.previous_items.append(next_item)

    def look_back(self, steps: int = 1)->SourceItem:
        '''Return the sequence value the given number of steps back. Do not
            move the iterator pointer position.

        Args:
            steps (int, optional): The number of steps to backwards for the
                desired item. steps must be a positive integer and must be
                less than the size of the previous_items queue. A value of 0
                will return the most recent item. Defaults to 1.
        Raises:
            BufferedIteratorValueError: Raised if "steps" cannot be converted
                to an integer, is less than 0.
        Returns:
            SourceLine: The desired previous source item.
        '''
        steps = self.check_steps(steps)
        return self.previous_items[-steps]

    def look_ahead(self, steps: int = 1)->SourceItem:
        '''Return the sequence value the given number of steps Ahead. Do not
            move the iterator pointer position.

        Args:
            steps (int, optional): The number of steps to forward for the
                desired item. steps must be a positive integer and must be
                less than the remaining size of the source. A value of 0
                will return the most recent item. Defaults to 1.
        Raises:
            BufferedIteratorValueError: Raised if "steps" cannot be converted
                to an integer, is less than 0.
        Returns:
            SourceLine: The desired previous source item.
        '''
        steps = self.check_steps(steps, backwards=False, skip=False)
        read_ahead = steps - len(self.future_items)
        if read_ahead > 0:
            if read_ahead > self.buffer_size:
                raise BufferedIteratorValueError(
                    f'look_ahead({steps}) exceeds the buffer_size. '
                    'Will not be able to retrieve all skipped items.')
            self.advance(read_ahead)
            self.backup(read_ahead)
        return self.future_items[steps-1]

    def goto_item(self, item_num: int, buffer_overrun=False):
        '''Move to item number item_num in the sequence.

        Adjust the iterator pointer so that the next item returned by a call to
        self.__next__ with be n_th item in the sequence. item_num is zero-based;
        the first item in the sequence is item "0".

        Args:
            item_num (int): The index number of the item in the sequence it be
                called next. item_num is zero-based; the first item in the
                sequence is item "0".
            buffer_overrun (bool, optional): If True do not check whether
                items will be lost from the buffer.
        '''
        current_item = self.item_count
        if current_item is None:
            raise BufferedIteratorValueError(
                'Iteration has not started. Cannot move to item')
        steps = current_item - item_num
        if steps == 0:
            logger.debug(
                f'Current item number is {current_item}. '
                f'Requested item is {item_num}.'
                'Already at requested item.')
        elif steps < 0:
            logger.debug(
                f'Current item number is {current_item}. '
                f'Requested item is {item_num}.'
                f'Advancing {-steps} item(s).')
            self.advance(-steps, buffer_overrun)
        else:
            logger.debug(
                f'Current item number is {current_item}. '
                f'Requested item is {item_num}. '
                f'Moving backwards {steps} item(s).')
            self.backup(steps)

    def link(self, other: BufferedIterator,
             include_previous_items=True,
             include_future_items=False):
        '''Copy certain buffer items from another instance.  Usually not called
            directly()

        Copy _step_back and _item_count properties from other.  Optionally copy
        previous and future queues from other. Used by the Section class to
        manage subsection iteration.

        Args:
            other (BufferedIterator): The BufferedIterator instance to copy
                    from.
            include_previous_items (bool, optional): If True, the previous items
                    dequeue from other replaces this instance's dequeue.
                    Otherwise, just clear the the previous items  dequeue.
                    Defaults to True.
            include_future_items (bool, optional): If True, the future items
                    dequeue from other replaces this instance's dequeue.
                    Otherwise, just clear the the future items  dequeue.
                    Defaults to False.
        Returns:
            None.
        '''
        #self.source_gen = iter(other.source_gen)
        self._step_back = other._step_back  # pylint: disable=protected-access
        self._item_count = other._item_count  # pylint: disable=protected-access
        # clear() and extend() allow for differing buffer sizes
        self.previous_items.clear()
        self.future_items.clear()
        if include_previous_items:
            self.previous_items.extend(other.previous_items)
        if include_future_items:
            self.future_items.extend(other.future_items)

    def update(self, source: 'BufferedIterator', buffer_overrun=True):
        '''Update the source pointer to match that of the supplied source.

        Adjust the position of the iterator to match the given source. It
        assumes that the given source is a copy of the current source, but at a
        different location in the iterator.

        Args:
            source (BufferedIterator, optional): A matching BufferedIterator,
                but at a  different location in the iterator
            buffer_overrun (bool, optional): If True do not check whether items
                will be lost from the buffer.  Default is True.
        '''
        if not isinstance(source, BufferedIterator):
            raise TypeError('source must be a BufferedIterator')
        if ('CLOSED' not in self.status) & ('CLOSED' not in source.status):
            index = source.item_count
            self.goto_item(index)
            logger.debug(f'Moving BufferedIterator to item #{index}')

    def __repr__(self)->str:
        '''Generate a string representation of a BufferedIterator instance.

        Returns:
            str: a string representation of this BufferedIterator instance
        '''
        class_name = self.__class__.__name__
        repr_str = ''.join([
            f'{class_name}(source={repr(self.source_gen)}, ',
            f'buffer_size={self.buffer_size})\n\t',
            f'{class_name}.previous_items = {repr(self.previous_items)}\n\t',
            f'{class_name}.future_items = {repr(self.future_items)}\n\t',
            f'{class_name}.item_count = {repr(self.item_count)}\n\t',
            f'{class_name}.status = {self.status}'
            ])
        return repr_str
