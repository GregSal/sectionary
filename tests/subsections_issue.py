# %% Subsections Issue

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

#%% Logging
import logging
logging.basicConfig(format='%(name)-20s - %(levelname)s: %(message)s')
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Text Processing')
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)
# %%  Read the Test Text File
#test_file = Path.cwd() / 'examples' / 'test_DIR_Data.txt'
#dir_text = test_file.read_text().splitlines()
#%%
raw_dir_text = '''
 Volume in drive C is Windows
 Volume Serial Number is DAE7-D5BA

 Directory of c:\\users\\...\\Test Dir Structure

2021-12-27  03:33 PM    <DIR>          .
2021-12-27  03:33 PM    <DIR>          ..
2021-12-27  04:03 PM    <DIR>          Dir1
2021-12-27  05:27 PM    <DIR>          Dir2
2016-02-25  09:59 PM                 3 TestFile1.txt
2016-02-15  06:46 PM                 7 TestFile2.rtf
2016-02-15  06:47 PM                 0 TestFile3.docx
2016-04-21  01:06 PM              3491 xcopy.txt
               4 File(s)           3501 bytes

 Directory of c:\\users\\...\\Test Dir Structure\Dir1

2021-12-27  04:03 PM    <DIR>          .
2021-12-27  04:03 PM    <DIR>          ..
2016-02-15  06:48 PM                 0 File in Dir One.txt
2021-12-27  03:45 PM    <DIR>          SubFolder1
2021-12-27  03:45 PM    <DIR>          SubFolder2
               1 File(s)              0 bytes
'''
dir_text = raw_dir_text.splitlines()
pprint(dir_text)
# %% DIR line processing functions
def dir_name_split(dir_line: str) -> str:
    '''Extract the folder name from the full path.

    Args:
        dir_line (str): The directory path line from a DIR folder listing.

    Returns (str): A tab delimited line with 'Folder Name:' before the tab and
        the folder name after the tab.
    '''
    output_line = 'Folder Name:\t' + dir_line.rsplit('\\', 1)[1]
    return output_line


def file_count_split(dir_line: str) -> str:
    '''Extract the number of files from the "File(s)" DIR line.

    Args:
        dir_line (str): The "File(s)" line from a DIR folder listing.

    Returns (str): A tab delimited line with 'Number of Files:' before the tab
        and the extracted number of files after the tab.
    '''
    output_line = 'Number of Files:\t' + dir_line.strip().split(' ', 1)[0]
    return output_line


def get_file_name(dir_line: str) -> str:
    '''Extract the name of the file or subdirectory from a DIR line.

    Args:
        dir_line (str): A main listing line from a DIR folder listing.

    Returns (str): A tab delimited line with 'File:' or 'Subdirectory:'before
        the tab and the extracted name of the file or subdirectory after
        the tab.
    '''
    if len(dir_line) < 39:  # This deals with blank lines.
        output_line = ''
    elif '<DIR>' in dir_line:  # Contains a subdirectory name.
        output_line = '\tSubdirectory:\t' + dir_line[39:]
    else:  # Contains a file name.
        output_line = '\tFile:\t\t' + dir_line[39:]
    return output_line

# %% Sub-Section Definitions
dir_section = Section(
    section_name='DirectoryName',
    #start_section='Directory of',
    end_section=SectionBreak(True)
    #processor=[dir_name_split]
    )

files_section = Section(
    section_name='NumberOfFiles',
    #start_section='File(s)',
    end_section=SectionBreak(True)
    #processor=[file_count_split]
    )


filename_section = Section(
    section_name='FileNames',
    #start_section=SectionBreak('Directory of', break_offset='After'),
    end_section=SectionBreak('File(s)', break_offset='Before')
    #processor=[get_file_name]
    )

# %%  Combined Section Definition
dir_section = Section(
    section_name='Full Directory',
    start_section='Directory of',
    end_section=SectionBreak('File(s)', break_offset='After'),
    subsections=[dir_section, filename_section, files_section]
    )

pprint(dir_section.read(dir_text))
# FIXME List of subsections returning None

#pprint(dir_text)
#for line in dir_text[3:20]:
 #   pprint('\t', line)
#%%
# Test data
GENERIC_TEST_TEXT = [
    'StartSection Name:         A',
    'A Content1:a',
    'B Content1:b',
    'C Content1:c',
    'EndSection Name:A',
    'End Of Section',
    'More text'
    ]


# %% Sub-Section Definitions
name_section = Section(
    section_name='Name',
    end_section=SectionBreak(True)
    )
content_section = Section(
    section_name='Content',
    end_section=SectionBreak('EndSection', break_offset='Before')
    )
end_section = Section(
    section_name='End',
    end_section=SectionBreak(True)
    )
full_section = Section(
    section_name='Full',
    start_section=SectionBreak('StartSection', break_offset='Before'),
    end_section=SectionBreak('End Of Section', break_offset='After'),
    subsections=[name_section, content_section, end_section]
    )

pprint(full_section.read(GENERIC_TEST_TEXT))

# %%
