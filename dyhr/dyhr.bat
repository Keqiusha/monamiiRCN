@Echo Off
REM activate Python venv
CALL "d:\ProgramData\Miniconda3\Scripts\activate.bat"
CD "D:\Project\Python\dyhr"
CALL "D:\ProgramData\Miniconda3\python.exe" "D:\ProgramData\Miniconda3\pkgs\scrapy-1.6.0-py37_0\Scripts\scrapy-script.py" runspider dyhr.py
conda deactivate
CALL "exit"