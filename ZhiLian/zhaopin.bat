@Echo Off
REM activate Python venv
CALL "d:\ProgramData\Miniconda3\Scripts\activate.bat"
CD "D:\Project\Python\dyhr"
CALL "D:\ProgramData\Miniconda3\python.exe" "D:\ProgramData\Miniconda3\pkgs\scrapy-1.6.0-py37_0\Scripts\scrapy-script.py" runspider zhaopin.py
conda deactivate
CALL "exit"
scrapy runspider main.py -a table_name=51job -a webhook_url="https://oapi.dingtalk.com/robot/send?access_token=43809228a987c62b02f707077c1785d511a7996a7614be2ae0ceda169dd325db"