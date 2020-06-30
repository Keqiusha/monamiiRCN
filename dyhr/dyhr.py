import logging
import sys

from scrapy.exceptions import CloseSpider

import email_service

sys.path.append('..')
import company
import db
import webhook
import scrapy
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher


class MainSpider(scrapy.Spider, db.MydbOperator):
    name = 'DyHR Spider'
    email_content = ''
    # start_urls = ['http://www.dyhr.cn/index.php?m=&c=jobs&a=jobs_list&key=%E5%A4%96%E8%B4%B8']
    start_urls = ['https://www.dyhr.cn/index.php/content/jobs?act=AIX_jobslist&key=%E5%A4%96%E8%B4%B8&lng=&lat=&ldLng=&ldLat=&ruLng=&ruLat=']
    # mydb = db.MydbOperator()
    emailService = email_service.EmailService()
    SITE_NAME = "DYHR"

    def __init__(self, table_name='', webhook_url='', **kwargs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.mydb = db.MydbOperator(table_name)
        print(webhook_url)
        self.webhook_service = webhook.WebHook(webhook_url)
        self.mydb.create_table()
        self.isInitialize = self.mydb.is_empty_table()
        print(self.isInitialize)
        self.page_limit = 5
        super().__init__(**kwargs)
    def parse(self,response):
        for company_info in response.selector.xpath("//div[@class='plist']//a[@class='line_substring']"):
            job_title = company_info.xpath("//div[@class ='td-j-name']//@title").get()
            company_name = company_info.css("::text").get()
            # company_url = "http://www.dyhr.cn" + company_info.xpath("@href").get()
            company_url = company_info.xpath("@href").get()
            location = "江苏丹阳"
            company_in_db = self.mydb.getByCompanyName(company_name)
            if company_in_db is None:
                company_obj = company.company(job_title, company_name, company_url, location)
                self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
                self.mydb.save_company(company_obj)
                # 添加 webhook发送器
                if not self.isInitialize:
                    formatted_context = self.webhook_service.format_with_template(company_obj)
                    print(formatted_context)
                    self.webhook_service.send_markdown(company_name, formatted_context, True)
            else:
                # Quit as reaching existing data records
                logging.info("Found existing record, hence quite.")
                raise CloseSpider("There's no new record yet.")
                # if not any(self.SITE_NAME in from_site for from_site in company_in_db[3].split(",")):
                #     siteName = company_in_db[3] + "," + self.SITE_NAME
                #     company_obj = company.company(job_title, company_name, company_url, location)
                #     self.mydb.updateCompany(company_obj)

        for next_page in response.selector.xpath("//div[@class='qspage']/a[contains(text(),'下一页')]"):
            nextPageSelector = next_page.css(".unable").get()
            if nextPageSelector is None:
                yield response.follow(next_page, self.parse)
            else:
                if self.email_content != '':
                    self.emailService.sendEmail(self.email_content)

    def spider_closed(self, spider):
        self.mydb.close()