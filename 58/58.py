import logging
import sys
from scrapy.exceptions import CloseSpider
sys.path.append('..')
import email_service
import company
import db
import webhook
import scrapy
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher



class MainSpider(scrapy.Spider, db.MydbOperator):
    name = '58DY Spider'
    email_content = ''
    # start_urls = ['https://nanjing.58.com/job/?key=%E5%A4%96%E8%B4%B8&classpolicy=main_null,job_A&final=1&jump=1']
    emailService = email_service.EmailService()
    SITE_NAME = "58DY"
    def __init__(self, table_name='', webhook_url='',site=[''], location = '', **kwargs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.start_urls = [
            f'https://{site}.58.com/job/?key=%E5%A4%96%E8%B4%B8&classpolicy=main_null,job_A&final=1&jump=1']
        self.mydb = db.MydbOperator(table_name)
        print(webhook_url)
        self.webhook_service = webhook.WebHook(webhook_url)
        self.mydb.create_table()
        self.isInitialize = self.mydb.is_empty_table()
        print(self.isInitialize)
        self.location = location
        self.page_limit = 5
        super().__init__(**kwargs)
    def parse(self, response):
        for company_info in response.selector.xpath("//ul[@id='list_con']//li[contains(@class,'job_item')]//div[@class='comp_name']//a"):
        # for company_info in response.selector.xpath("//ul[@id='list_con']//li[contains(@class,'job_item')]"):
            job_title = company_info.xpath("//span[@class = 'cate']//text()").get()
            print("***********************")
            print(job_title)
            company_name = company_info.xpath("@title").get()
            print(company_name)
            company_url = company_info.xpath("@href").get()
            print(company_url)
            location = self.location
            print(location)
            print("##############")
            company_in_db = self.mydb.getByCompanyName(company_name)
            if company_in_db is None:
                company_obj = company.company(job_title, company_name, company_url, location)
                # self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
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
                #     companyObj = company.company(company_name, company_url, siteName)
                #     self.mydb.updateCompany(companyObj)
                # if not any(self.SITE_NAME in from_site for from_site in company_in_db[3].split(",")):
                #     siteName = company_in_db[3] + "," + self.SITE_NAME
                #     company_obj = company.company(job_title, company_name, company_url, location)
                #     self.mydb.updateCompany(company_obj)
        for next_page in response.selector.xpath("//div[@class='pagesout']/a[contains(@class,'next')]"):
            nextPageSelector = next_page.css(".disabled").get()
            if nextPageSelector is None:
                yield response.follow(next_page, self.parse)
            else:
                if self.email_content != '':
                    self.emailService.sendEmail(self.email_content)
    def spider_closed(self, spider):
        self.mydb.close()
