#!/bin/bash
log_path="/var/log/HR/"
log_file_name="58"
ext=".log"
DATE=$(date +%Y-%m-%d)
log_file=${log_path}${log_file_name}.${DATE}${ext}
cd /usr/local/HR/58/
source ../python_venv/bin/activate
scrapy runspider 58.py -a location=南京 -a site=nanjing -a table_name=58NJ -a webhook_url="https://oapi.dingtalk.com/robot/send?access_token=3ed777a16f47a6c625149744c1993b3d2eef4f11dff72e09c1b4913455c882c5" --logfile ${log_file}
scrapy runspider 58.py -a location=镇江 -a site=zhenjiang -a table_name=58NJ -a webhook_url="https://oapi.dingtalk.com/robot/send?access_token=674738e133f0d8fc2580e3f5c71f8ecb26f47b02786e0055ff9986e876de4db8" --logfile ${log_file}