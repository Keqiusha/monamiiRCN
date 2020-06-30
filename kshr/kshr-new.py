import random
import json
from scrapy.http import HtmlResponse
import sys
import email_service
sys.path.append('..')
import company
import db
import webhook
import scrapy
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher


class Sequential_MainSpider(scrapy.Spider, db.MydbOperator):
    name = 'KSHR Spider'
    email_content = ''
    start_url = 'http://kshr.com.cn/handler/CommonDataHandler.ashx?t='
    # mydb = db.MydbOperator()
    emailService = email_service.EmailService()
    SITE_NAME = "kshr"
    pageNo = 1
    form_request_payload = {"Industry": "", "Area": "", "PFun": "", "MonthSalary": "", "CompanyProperty": "", "CompanyScale": "", "Degree": "", "WorkYear": "", "Sex": "", "PublishTime": "", "OrderbySalary": "", "CurrentPage": pageNo, "KeyType": "all", "KeyWord": "外贸"}
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
            yield scrapy.FormRequest(self.start_url + str(random.random()), 
                                        method="POST",
                                        body='parm=' + str(self.form_request_payload) + '&m=getposition', 
                                        headers={
                                            'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8',
                                            'Referer':'http://kshr.com.cn/CacheSearch.aspx?keyword=%E5%A4%96%E8%B4%B8&strtype=all',
                                            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
                                            'X-Requested-With': 'XMLHttpRequest'
                                            },
                                        callback=self.parse, 
                                        errback=self.errback_httpbin, 
                                        dont_filter=True)
    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

    def parse(self,response):
        self.logger.debug("Current Page:" + str(self.pageNo))
        result_json = json.loads(response.text)
        if result_json['ResultPageCount'] > 0:
            response = HtmlResponse(url=self.start_url, body=result_json['ResultHtml'], encoding='utf-8')
            selectors = response.selector.xpath("//div[contains(@class,'data-fy')]//div[contains(@class, 'yp-search-list')]//p//a")
            if selectors:
                for company_info in selectors:
                    location = "暂未开放"
                    company_name = company_info.css("::text").get()
                    company_url = "http://kshr.com.cn" + company_info.xpath("@href").get()
                    job_title = "暂未开放"
                    company_in_db = self.mydb.getByCompanyName(company_name)
                    if company_in_db is None:
                        company_obj = company.company(job_title, company_name, company_url, location)
                        self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
                        self.mydb.save_company(company_obj)
                        # 添加 webhook发送器
                        if self.isInitialize:
                            formatted_context = self.webhook_service.format_with_template(company_obj)
                            print(formatted_context)
                            self.webhook_service.send_markdown(company_name, formatted_context, True)
                    else: 
                        if not any(self.SITE_NAME in from_site for from_site in company_in_db[3].split(",")):
                            siteName = company_in_db[3] + "," + self.SITE_NAME
                            company_obj = company.company(job_title, company_name, company_url, location)
                            self.mydb.updateCompany(company_obj)

            last_page = response.selector.xpath("//div[@data-xh][last()]/@data-xh").get()
            if(int(last_page) == self.pageNo):
                self.logger.debug("Page crawling finished...")
                return

            self.pageNo+=1
            self.form_request_payload['CurrentPage']=self.pageNo

            yield scrapy.FormRequest(self.start_url + str(random.random()), 
                                        method="POST",
                                        body='parm=' + str(self.form_request_payload) + '&m=getposition', 
                                        headers={
                                            'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8',
                                            'Referer':'http://kshr.com.cn/CacheSearch.aspx?keyword=%E5%A4%96%E8%B4%B8&strtype=all',
                                            'X-Requested-With': 'XMLHttpRequest'
                                            },
                                        callback=self.parse, 
                                        errback=self.errback_httpbin, 
                                        dont_filter=True)
    
    def spider_closed(self, spider):
        if self.email_content != '':
            self.emailService.sendEmail(self.email_content)
        self.mydb.close()
            
        

