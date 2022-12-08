rem ########## VS Code Launch ############
rem set WORKSPACE_FOLDER="%HOMEPATH%\OneDrive - Queen's University\Python\Projects\sectionary package"
set WORKSPACE_FOLDER="D:\OneDrive - Queen's University\Python\Projects\sectionary package"
set WORKSPACE_FILE="%WORKSPACE_FOLDER%\sectionary.code-workspace"

CALL C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3
CALL conda activate sectionaryDev
Cd "%WORKSPACE_FOLDER%"
D:
CALL code sectionary.code-workspace
EXIT