'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
from __future__ import annotations
from collections import deque
from typing import Sequence, TypeVar
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
    '''Raised when BufferedIterator peak will cause unyielded
        lines to be dropped.
    '''


#%% Classes
class BufferedIterator():
    '''Iterate through sequence allowing for backup and look ahead.
    '''
    def __init__(self, source: Sequence[SourceItem], buffer_size=5):
        self.buffer_size = buffer_size
        self.source_gen = iter(source)
        self.previous_items = deque(maxlen=buffer_size)
        self.future_items = deque(maxlen=buffer_size)
        self._step_back = 0
        return

    def get_next_item(self) -> SourceItem:
        '''
        Get the next item from the source.

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
            logger.debug(f'Getting item: {next_item}\t from future_items')
        else:
            # Get the next item from the source iterator
            try:
                # Read from the iterator source
                next_item = self.source_gen.__next__()
            except (StopIteration, RuntimeError) as eof:
                # Treat "StopIteration" or "RuntimeError" exceptions as
                # End-of-File indicators.
                raise BufferedIteratorEOF from eof
            logger.debug(f'Getting item: {next_item}\t from source')
        return next_item

    def __next__(self) -> SourceItem:
        '''Return the next item in a sequence allowing for retracing steps.

        Calls get_next_item checking for "BufferedIteratorEOF" and
           propagating the exception.  As each item is obtained from the source
           it is added to the "previous_items" queue to allow for moving
           backwards through the source.

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
        '''Check the steps value.

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
            BufferedIteratorValueError: Indicates and invalid "steps" value.
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

    def rewind(self):
        '''
        Move the iterator pointer back the number of steps set in the
        "step_back" property.

        The appropriate number of items in the "previous_items" queue are
           moved to the "future_items" queue and the "step_back" property is
           reset to 0.
        Returns:
            None.
        '''
        for step in range(self._step_back): # pylint: disable=unused-variable
            self._step_back -= 1
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
        self._step_back = steps
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

    def advance(self, steps: int = 1):
        '''Move "steps" forward through the items in source.

        Move the iterator pointer forward the given number of steps
           storing the items in between as if they had been returned.  The
           items passed over can be retrieved with backup or look_back.

        Args:
            steps (int, optional): The number of items to advance in the in
                the source.  A value of zero will be ignored.  Float values
                will be truncated to integers. Defaults to 1
        Raises:
            BufferedIteratorValueError: Raised if "steps" cannot be converted
                to an integer or is less than 0.
        Returns:
            None.
        '''
        steps = self.check_steps(steps, backwards=False, skip=False)
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
        steps = self.check_steps(steps)
        read_ahead = steps - len(self.future_items)
        if read_ahead > 0:
            if read_ahead > self.buffer_size:
                raise BufferedIteratorValueError(
                    f'look_ahead({steps}) exceeds the buffer_size. '
                    'Will not be able to retrieve all skipped items.')
            self.advance(read_ahead)
            self.backup(read_ahead)
        return self.future_items[steps-1]

    def update(self, other: BufferedIterator, include_items=True):
        '''Copy buffer items from another instance.

        Copy step_back property from other.  Optionally copy previous and
            future queues from other.  No testing is done before copying.

        Args:
            other (BufferedIterator): The BufferedIterator instance to copy
                from.
            include_items (bool, optional): If True, previous and
                future queues from other replace this instances queues.
                Otherwise, just replace the step_back property with the value
                from other. Defaults to True.
        Returns:
            None.
        '''
        self._step_back = other._step_back  # pylint: disable=protected-access
        if include_items:
            self.previous_items = other.previous_items.copy()
            self.future_items = other.future_items.copy()

    def __repr__(self):
        class_name = self.__class__.__name__
        repr_str = ''.join([
            f'{class_name}(source={repr(self.source_gen)}, ',
            f'buffer_size={self.buffer_size})\n\t',
            f'{class_name}.previous_items = {repr(self.previous_items)}\n\t',
            f'{class_name}.future_items = {repr(self.future_items)}\n\t',
            f'{class_name}._step_back = {self._step_back}'
            ])
        return repr_str
