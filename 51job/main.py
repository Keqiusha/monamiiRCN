import sys
sys.path.append('..')
import logging
import company
import db
import webhook
import scrapy
from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.xlib.pydispatch import dispatcher


class MainSpider(scrapy.Spider, db.MydbOperator):
    name = '51JOB Spider'
    email_content = ''
    # 外贸 + 镇江 + 1周内
    # 如果搜索多个地址，用“，”隔开，最多可添加5个城市
    start_urls = [
        'https://search.51job.com/list/071000,000000,0000,00,2,99,%25E5%25A4%2596%25E8%25B4%25B8,2,1.html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=1&dibiaoid=0&line=&welfare=']
    # mydb = db.MydbOperator()
    # emailService = email_service.EmailService()
    SITE_NAME = "51JOB"

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

    def parse(self, response):
        for record in response.selector.xpath("//div[@class='dw_table']//div[@class='el']"):
            job_title = record.xpath(".//p[contains(@class, 't1')]//a//text()").get().strip()
            company_info = record.xpath(".//span[@class='t2']//a")
            print(company_info)
            company_name = company_info.css("::text").get()
            company_url = company_info.xpath("@href").get()
            location = record.xpath(".//span[@class='t3']//text()").get()
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
                #     companyObj = company.company(company_name, company_url, siteName)
                #     self.mydb.updateCompany(companyObj)

        for next_page in response.selector.xpath("//div[@class='dw_page']//a[contains(text(),'下一页')]"):
            current_page = response.selector.xpath("//div[@class='dw_page']//li[@class='on']//text()").get()
            if int(current_page) <= self.page_limit:
                yield response.follow(next_page, self.parse)

        # for end_page in response.selector.xpath("//div[@class='dw_page']//span[contains(text(),'下一页')]"):
        #     if end_page is not None:
        #         if self.email_content != '':
        #             self.emailService.sendEmail(self.email_content)

    def spider_closed(self, spider):
        self.mydb.close()
