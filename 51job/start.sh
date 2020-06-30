#!/bin/bash
log_path="/var/log/HR/"
log_file_name="51job"
ext=".log"
DATE=$(date +%Y-%m-%d)
log_file=${log_path}${log_file_name}.${DATE}${ext}
cd /usr/local/HR/51job/
source ../python_venv/bin/activate
scrapy runspider main.py -a table_name=51job -a webhook_url="https://oapi.dingtalk.com/robot/send?access_token=43809228a987c62b02f707077c1785d511a7996a7614be2ae0ceda169dd325db" --logfile ${log_file}