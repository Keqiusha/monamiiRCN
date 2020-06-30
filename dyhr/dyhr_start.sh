#!/bin/bash
log_path="/var/log/HR/"
log_file_name="dyhr"
ext=".log"
DATE=$(date +%Y-%m-%d)
log_file=${log_path}${log_file_name}.${DATE}${ext}
cd /usr/local/HR/dyhr/
source ../python_venv/bin/activate
scrapy runspider dyhr.py -a table_name=dyhr -a webhook_url="https://oapi.dingtalk.com/robot/send?access_token=98b5f19441e157d1a8cf9d782d92f520b0c686c008dfae4e1603d615926d1cbd" --logfile ${log_file}