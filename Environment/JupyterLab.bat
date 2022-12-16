rem ########## Jupyter Lab Launch ############
rem Set relevant paths
rem WORKSPACE_FOLDER="%HOMEPATH%\OneDrive - Queen's University\Python\Projects\sectionary package"
set WORKSPACE_FOLDER="D:\OneDrive - Queen's University\Python\Projects\sectionary package"
set SOURCE_FOLDER="%WORKSPACE_FOLDER%\src"
set TEST_FOLDER="%WORKSPACE_FOLDER%\Tests"
set EXAMPLES_FOLDER="%WORKSPACE_FOLDER%\Tests"

rem ########### Add folder to PYTHONPATH ##########
rem Windows truncates PATH to 1024 characters.
rem Make a backup of PATH before any modifications.
rem Backup of Path
echo %PYTHONPATH% > C:\temp\pythonpath-backup.txt

set PYTHONPATH="%PYTHONPATH%;%WORKSPACE_FOLDER%;%SOURCE_FOLDER%;%TEST_FOLDER%;%EXAMPLES_FOLDER%"
echo %PYTHONPATH%
call C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3
call conda activate sectionaryDev
call jupyter-lab %WORKSPACE_FOLDER%
EXIT
