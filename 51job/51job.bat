@Echo Off
REM activate Python venv
CALL "D:\Anaconda\envs\monamiiRFQ\Scripts\activate.bat"
CD "D:\scrapy_project\HR\51job"
CALL "D:\ProgramData\Miniconda3\python.exe" "D:\ProgramData\Miniconda3\pkgs\scrapy-1.6.0-py37_0\Scripts\scrapy-script.py" runspider 51job.py
conda deactivate
CALL "exit"