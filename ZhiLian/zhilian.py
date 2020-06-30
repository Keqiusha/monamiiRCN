import logging
import os
import sys
import time

from furl import furl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
sys.path.append('..')
import webhook
import db
import company
import webdriver_chrome
import scrapy
from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.xlib.pydispatch import dispatcher
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log as urllibLogger
class MainSpider(scrapy.Spider, db.MydbOperator):
    LOGGER.setLevel(logging.WARNING)
    urllibLogger.setLevel(logging.WARNING)
    SITE_NAME = "ZhiLian"
    name = 'Zhilian Spider'
    def __init__(self,table_name='', webhook_url='', **kwargs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.start_urls = [f'https://fe-api.zhaopin.com/c/i/sou?pageSize=200&cityId=664&workExperience=-1&education=5&companyType=-1&employmentType=-1&jobWelfareTag=-1&kw=python&kt=3']
        # self.start_urls = url
        self.mydb = db.MydbOperator(table_name)
        option = ChromeOptions()
        tmp_path = './tem_path'
        prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': tmp_path,
                 "profile.default_content_setting_values.automatic_downloads": 1}  # 允许多个文件下载
        option.add_experimental_option('prefs', prefs)
        option.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.driver = webdriver.Chrome(options=option, executable_path="../bin/driver/chromedriver.exe")
        # self.driver = webdriver_chrome.gen_browser('../bin/driver/chromedriver.exe')
        self.webhook_service = webhook.WebHook(webhook_url)
        self.mydb.create_table()
        self.isInitialize = self.mydb.is_empty_table()
        self.page_limit = 5
        # script = 'Object.defineProperty(navigator,"webdriver",{get:() => false,});'
        #         # # 运行Javascript
        #         # self.driver.execute_script(script)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })
        super().__init__(**kwargs)
    def parse(self, response):
        print("#########################")
        print(response.url)
        self.driver.get(response.url)
        element = self.driver.find_element_by_css_selector('body > div.a-modal.risk-warning > div > div > button')
        element.click()
        time.sleep(50)
        print(response.url)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "contentpile__content__wrapper clearfix"))
            )
            time.sleep(50)
            container_elements = self.driver.find_elements_by_xpath("//div[@class='contentpile__content__wrapper__item clearfix']")
            for container_element in container_elements:
                job_title = container_element.find_element_by_xpath("//span[@class='contentpile__content__wrapper__item__info__box__jobname__title']//@title")
                print(job_title)
                location = container_element.find_element_by_xpath("//li[1][@class='contentpile__content__wrapper__item__info__box__job__demand__item']")
                print(location)
                company_name = container_element.find_element_by_xpath("//a[@class='contentpile__content__wrapper__item__info__box__cname__title company_title']//@title")
                company_url = container_element.find_element_by_xpath("//a[@class='contentpile__content__wrapper__item__info__box__cname__title company_title']//@href")
                company_in_db = self.mydb.getByCompanyName(company_name)
                if company_in_db is None:
                    company_obj = company.company(job_title, company_name, company_url, location)
                    self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
                    self.mydb.save_company(company_obj)
                else:
                    logging.info("Found existing record, hence quite.")
                    raise CloseSpider("There's no new record yet.")
        except:
            print("进入网站失败!")
    def spider_closed(self, spider):
        self.mydb.close()
        self.driver.close()