import unittest
from pathlib import Path
import re

from sections import Section, SectionBreak


#TODO convert every sage in Example MS Dir Output.ipynb to a test
#%% Test data
test_text = '''
Volume in drive C has no label.
 Volume Serial Number is 56DB-14A7

 Directory of C:\\Text Files\\Test Dir Structure

2021-06-18  14:54    <DIR>          .
2021-06-18  14:54    <DIR>          ..
2021-06-18  14:54    <DIR>          Dir1
2021-06-18  14:54    <DIR>          Dir2
2016-02-25  22:59                 3 TestFile1.txt
2016-02-15  19:46                 7 TestFile2.rtf
2016-02-15  19:47                 0 TestFile3.docx
2016-04-21  14:06              3491 xcopy.txt
               4 File(s)           3501 bytes

'''
dir_text = test_text.splitlines()
#%%
dir_section = Section(start_section='Directory of', end_section='File(s)')
print(dir_section.read(dir_text))

#%%
dir_section = Section(start_section='Directory of',
                      end_section=SectionBreak('File(s)', break_offset='After'))
print(dir_section.read(dir_text))

#%%
def process_directory(dir_line):
    # Get the directory name
    if 'Directory of' in dir_line:
        output_line = 'Folder Name:\t' + dir_line.rsplit('\\', 1)
    # Label the subdirectories
    elif '<DIR>' in dir_line:
        output_line = '\tSubdirectory:\t' + dir_line[36:]
    # Label the file counts
    elif 'File(s)' in dir_line:
        output_line = '\tNumber of Filesa:\t' + dir_line.trim().split(' ', 1)
    # Label the files
    else:
        output_line = '\tFile:\t' + dir_line[36:]
    return output_line

for line in dir_text:
    print(process_directory(line))


def dir_name_split(line):
    return ['Folder Name:', line.rsplit('\\', 1)[1]]
dir_name_rule = Rule('Directory of', pass_method=dir_name_split)

def file_count_split(line):
    return ['Number of Files:', line.strip().split(' ', 1)[0]]
file_count_rule = Rule('File(s)', pass_method=file_count_split)

def subfolder(line):
    return ['Subdirectory:', line[36:]]
subfolder_rule = Rule('<DIR>', pass_method=subfolder)

def file(line):
    return ['File:' + line[36:]]

dir_process = RuleSet([dir_name_rule, file_count_rule, subfolder_rule],
                      default=file)


dir_section = Section(start_section='Directory of',
                      end_section=SectionBreak('File(s)', break_offset='After'),
                      processor=[dir_process])

output = dir_section.read(dir_text)
for line in output:
    print(line)

#%%
#%%
dir_section.read(dir_text)
class TestSimpleTriggers(unittest.TestCase):

    def setUp(self):
        pass


    def test_end_section(self):
        pass
