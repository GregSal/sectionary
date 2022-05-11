'''Subsections Issue'''

# %% Imports
from typing import List
from pathlib import Path
from pprint import pprint
import re
import sys

import pandas as pd
import xlwings as xw

import text_reader as tp
from sections import Rule, RuleSet, SectionBreak, ProcessingMethods, Section

# %% Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Text Processing')
logger.setLevel(logging.DEBUG)


# %% 2-line Section Source

GENERIC_TEST_TEXT = [
    'Text to be ignored',
    'StartSection Name: A',
    'EndSection Name: A',
    'StartSection Name: B',
    'EndSection Name: B',
    'More text to be ignored',
    ]

# %%  Initial Section and Sub-Section Definitions
sub_section = Section(
    section_name='SubSection',
    #start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    #start_section=SectionBreak('StartSection', break_offset='Before'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
# - ![Good](../examples/Valid.png) Results in all lines in one sub-list
# %% Add start to Section Definition
# - Section start **Before** *StartSection*
# `start_section=SectionBreak('StartSection', break_offset='Before'),`

sub_section = Section(
    section_name='SubSection',
    #start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
# - ![Good](../examples/Valid.png) Includes all lines after first *StartSection* in single sub-list.
# %% Add end to Section Definition

sub_section = Section(section_name='SubSection')

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )

# - ![Good](../examples/Valid.png) Includes both lines of first section in single sub-list.
# %% Define Muti-Section to Read Both Sections

sub_section = Section(section_name='SubSection')

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )

multi_section = Section(
    section_name='Multi',
    subsections=[full_section]
    )
# - ![Bad](../examples/error.png) Includes both lines of each section in its own sub-list, but adds a blank sub-list at the end.
# %% Set Same Start and End Breaks for Section
full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('StartSection', break_offset='Before')
    )

multi_section = Section(section_name='Multi',
    subsections=[full_section]
    )
# - Without SubSection, it works as expected.

sub_section = Section(section_name='SubSection')

full_section = Section(section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('StartSection', break_offset='Before'),
    subsections=[sub_section]
    )

multi_section = Section(
    section_name='Multi',
    subsections=[full_section]
    )
# - ![Bad](../examples/error.png) Appears to hang
# %% SubSection Break Options
# %% Add *End on First* to Sub-Section
sub_section = Section(
    section_name='SubSection',

    end_on_first_item=True,
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
# - ![Bad](../examples/error.png) Results in `['EndSection Name: A']` sub-list, should have been `['StartSection Name: A']`.

# %% Add *End* as **True** to Sub-Section
sub_section = Section(
    section_name='SubSection',

    end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )

pprint(full_section.read(GENERIC_TEST_TEXT))

# %% What should  `end_section=SectionBreak(True)` result in?
# - ![Bad](../examples/error.png) Results in `['StartSection Name: A'], []` sub-lists, should have been `['StartSection Name: A']`.
# %% Add *Start* to Sub-Section
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before')

    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
# - ![Bad](../examples/error.png) Results in blank sub-list.
# %% Change Start Sub-Section to **After*

sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('StartSection', break_offset='After')
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )

pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Bad](../examples/error.png) Results in blank sub-list.
# %% [markdown]
# # DONE TO HERE
# %% [markdown]
# ### Add start to SubSection Definition
# > `start_section=SectionBreak('EndSection', break_offset='Before')`

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    #start_section=SectionBreak('StartSection', break_offset='Before'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Bad](../examples/Error.png) Results in Empty list of lists
# %% [markdown]
# ### Add *Start After* to Section Definition
# > `start_section=SectionBreak('StartSection', break_offset='After')`

# %%
sub_section = Section(
    section_name='SubSection',
    #start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='After'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Good](../examples/Valid.png) Results in one line section
# %% [markdown]
# ### Add *Start After StartSection* to Section Definition and *Start Before End Section* to SubSection Definition
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='After')`
# >
# > **SubSection Definition**<br>
# > `start_section=SectionBreak('EndSection', break_offset='Before')`
#

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='After'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Bad](../examples/error.png) Results in first and second section
# %% [markdown]
# ### Add *Start After StartSection* to Section Definition and *Start Before End Section* to SubSection Definition and set *End On First Line* for SubSection
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='After')`
# >
# > **SubSection Definition**<br>
# > `start_section=SectionBreak('EndSection', break_offset='Before'),`
# > `end_on_first_item=True,`
#

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='After'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Bad](../examples/Error.png) Results in second section
# %% [markdown]
# ### Add *Start After StartSection* to Section Definition, and for SubSection Definition, set *Start* to  *Before EndSection* and *End* to *`True` (Always Break)*
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='After')`
# >
# > **SubSection Definition**<br>
# > `start_section=SectionBreak('EndSection', break_offset='Before'),`
# > `end_section=SectionBreak(True),`
#

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='After'),
    #end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Good](../examples/Valid.png) Results in one line section
# %% [markdown]
# ### Add *Start After StartSection* and *End Before EndSection* to Section Definition, and for SubSection Definition, set *Start* to  *Before EndSection* and *End* to *`True` (Always Break)*
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='After'),`
# > `end_section=SectionBreak('EndSection', break_offset='After'),`
#
# >
# > **SubSection Definition**<br>
# > `start_section=SectionBreak('EndSection', break_offset='Before'),`
# > `end_section=SectionBreak(True),`
#

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='After'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Good](../examples/Valid.png) Results in one line section
# %% [markdown]
# ### Add *Start __Before__ StartSection* and *End Before EndSection* to Section Definition, and for SubSection Definition, set *Start* to  *Before EndSection* and *End* to *`True` (Always Break)*
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='Before'),`
# > `end_section=SectionBreak('EndSection', break_offset='After'),`
#
# >
# > **SubSection Definition**<br>
# > `start_section=SectionBreak('EndSection', break_offset='Before'),`
# > `end_section=SectionBreak(True),`
#

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Bad](../examples/Error.png) Results in empty list of lists
# %% [markdown]
# ### Add *Start __Before__ StartSection* and *End Before EndSection* to Section Definition, and for SubSection Definition, set *Start* to *Before EndSection*, *End* to *`True` (Always Break)* and *Keep Partial* to *`True`*
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='Before'),`
# > `end_section=SectionBreak('EndSection', break_offset='After'),`
# >
# > **SubSection Definition**<br>
# > `start_section=SectionBreak('EndSection', break_offset='Before'),`<br>
# > `end_section=SectionBreak(True),`<br>
# > `keep_partial=True,`
#

# %%
sub_section = Section(
    section_name='SubSection',
    start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    keep_partial=True,
    end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Bad](../examples/Error.png) Results in empty list of lists
# %% [markdown]
# ### Add *Start __Before__ StartSection* and *End Before EndSection* to Section Definition, and don't set any SectionBreaks for SubSection Definition,
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='Before'),`
# > `end_section=SectionBreak('EndSection', break_offset='After'),`
#

# %%
sub_section = Section(
    section_name='SubSection',
    #start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Good](../examples/Valid.png) Results in Two line section
# %% [markdown]
# ### Add *Start __After__ StartSection* and *End Before EndSection* to Section Definition, and don't set any SectionBreaks for SubSection Definition,
# > **Section Definition**<br>
# > `start_section=SectionBreak('StartSection', break_offset='After'),`
# > `end_section=SectionBreak('EndSection', break_offset='After'),`
#

# %%
sub_section = Section(
    section_name='SubSection',
    #start_section=SectionBreak('EndSection', break_offset='Before'),  # Added to use alone
    #end_on_first_item=True,
    #keep_partial=True,
    #end_section=SectionBreak(True)
    )

full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='After'),
    end_section=SectionBreak('EndSection', break_offset='After'),
    subsections=[sub_section]
    )
pprint(full_section.read(GENERIC_TEST_TEXT))

# %% [markdown]
# - ![Good](../examples/Valid.png) Results in one line section
