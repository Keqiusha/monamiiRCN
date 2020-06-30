import json
import random
import sys
sys.path.append('..')
import webhook
import scrapy
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.xlib.pydispatch import dispatcher
import company
import db
import email_service


class MainSpider(scrapy.Spider, db.MydbOperator):
    name = 'KSHR Spider'
    email_content = ''
    start = 0
    totalSize = 0
    start_url = 'https://fe-api.zhaopin.com/c/i/sou?pageSize=90&cityId=646&salary=0,0&workExperience=-1&education=-1&companyType=-1&employmentType=-1&jobWelfareTag=-1&kw=%E5%A4%96%E8%B4%B8&kt=3&=0&_v=0.55545747&x-zp-page-request-id=df3b86ad2bca4742ad84253e0958c6e5-1562992810274-844145&x-zp-client-id=5c977c9d-c1ee-4c67-b475-97de3b07b16c'
    # mydb = db.MydbOperator()
    emailService = email_service.EmailService()
    SITE_NAME = "ZhiLian"
    download_timeout = 20

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

    def start_requests(self):
            yield scrapy.Request(self.start_url,
                                        method="GET",
                                        headers={
                                            'Referer':'https://sou.zhaopin.com/?jl=646&sf=0&st=0&kw=%E5%A4%96%E8%B4%B8&kt=3',
                                            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
                                            },
                                        callback=self.parse,
                                        errback=self.errback_httpbin,
                                        dont_filter=True)
    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

    def parse(self,response):
        result_json = json.loads(response.text)
        if result_json['code'] == 200 and result_json['data']['count'] > 0:
            if (self.start == 0): 
                self.totalSize= result_json['data']['count']

            for company_info in result_json['data']['results']:
                job_title = "暂未开放"
                location = "暂未开放"
                company_name = company_info['company']['name']
                company_url = company_info['company']['url']
                company_in_db = self.mydb.getByCompanyName(company_name)
                if company_in_db is None:
                    company_obj = company.company(job_title, company_name, company_url, location)
                    self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
                    self.mydb.save_company(company_obj)
                else: 
                    if not any(self.SITE_NAME in from_site for from_site in company_in_db[3].split(",")):
                        siteName = company_in_db[3] + "," + self.SITE_NAME
                        company_obj = company.company(company_name, company_url, siteName)
                        self.mydb.updateCompany(company_obj)

            if (self.start + 90 <= self.totalSize):
                self.start += 90
                follow_url = 'https://fe-api.zhaopin.com/c/i/sou?start=' + str(self.start) + '&pageSize=90&cityId=646&salary=0,0&workExperience=-1&education=-1&companyType=-1&employmentType=-1&jobWelfareTag=-1&kw=%E5%A4%96%E8%B4%B8&kt=3&=0&_v=0.55545747&x-zp-page-request-id=df3b86ad2bca4742ad84253e0958c6e5-1562992810274-844145&x-zp-client-id=5c977c9d-c1ee-4c67-b475-97de3b07b16c'

                yield scrapy.Request(follow_url, 
                                        method="GET",
                                        headers={
                                            'Referer':'https://sou.zhaopin.com/?jl=646&sf=0&st=0&kw=%E5%A4%96%E8%B4%B8&kt=3',
                                            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
                                            },
                                        callback=self.parse, 
                                        errback=self.errback_httpbin, 
                                        dont_filter=True)

    def spider_closed(self, spider):
        if self.email_content != '':
            self.emailService.sendEmail(self.email_content)
        self.mydb.close()
