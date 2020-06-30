import sys
sys.path.append('..')
import scrapy
import company
import db
import email_service
import random
import json
from scrapy.http import HtmlResponse
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher


class Parallel_MainSpider(scrapy.Spider, db.MydbOperator):
    name = 'KSHR Spider'
    email_content = ''
    start_url = 'http://kshr.com.cn/handler/CommonDataHandler.ashx?t='
    mydb = db.MydbOperator()
    emailService = email_service.EmailService()
    SITE_NAME = "kshr"
    pageNo = 1
    form_request_payload = {"Industry": "", "Area": "", "PFun": "", "MonthSalary": "", "CompanyProperty": "", "CompanyScale": "", "Degree": "", "WorkYear": "", "Sex": "", "PublishTime": "", "OrderbySalary": "", "CurrentPage": pageNo, "KeyType": "all", "KeyWord": "外贸"}
    download_timeout = 30
    def __init__(self):
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def start_requests(self):
        while self.pageNo < 20:
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
            self.pageNo+=1
            self.form_request_payload['CurrentPage']=self.pageNo

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

    def parse(self,response):
        result_json = json.loads(response.text)
        if result_json['ResultPageCount'] > 0:
            response = HtmlResponse(url=self.start_url, body=result_json['ResultHtml'], encoding='utf-8')
            selectors = response.selector.xpath("//div[contains(@class,'data-fy')]//div[contains(@class, 'yp-search-list')]//p//a")
            if selectors:
                for company_info in selectors:
                    company_name = company_info.css("::text").get()
                    company_url = company_info.xpath("@href").get()
                    company_in_db = self.mydb.getByCompanyName(company_name)
                    if company_in_db is None:
                        companyObj = company.company(company_name, company_url, self.SITE_NAME)
                        self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
                        self.mydb.saveCompany(companyObj)
                    else: 
                        if not any(self.SITE_NAME in from_site for from_site in company_in_db[3].split(",")):
                            siteName = company_in_db[3] + "," + self.SITE_NAME
                            companyObj = company.company(company_name, company_url, siteName)
                            self.mydb.updateCompany(companyObj)
    
    def spider_closed(self, spider):
        if self.email_content != '':
            self.emailService.sendEmail(self.email_content)
            self.logger.info("Sending Email...")
        self.mydb.close()
            
        

