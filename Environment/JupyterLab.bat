rem ########## Jupyter Lab Launch ############
set WORKSPACE_FOLDER="%HOMEPATH%\OneDrive - Queen's University\Python\Projects\sectionary package"
call C:\ProgramData\Anaconda3\Scripts\activate.bat C:\ProgramData\Anaconda3
call conda activate sectionaryDev
call jupyter-lab %WORKSPACE_FOLDER%
EXIT
