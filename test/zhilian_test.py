import logging
import time

import selenium
import scrapy
from scrapy.extensions.closespider import CloseSpider
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
        TimeoutException,
        WebDriverException,
        NoSuchElementException,
        StaleElementReferenceException,
    )
from .. import db, webhook, company
class MainSpider(scrapy.Spider, db.MydbOperator):
    name = 'testSpider'
    def __init__(self, webhook_url='', table_name='', **kwargs):
        self.webhook_url = webhook_url
        self.start_urls = [f'https://sou.zhaopin.com/?jl=635&kw=%E5%A4%96%E8%B4%B8&kt=3']
        self.table = table_name
        self.mydb = db.MydbOperator(table_name)
        self.driver = webdriver.Chrome('../bin/driver/chromedriver.exe')
        self.webhook_service = webhook.WebHook(webhook_url)
        super().__init__(**kwargs)
    def parse(self, response):
        self.driver.get(self.start_urls)
        element = self.driver.find_element_by_css_selector('body > div.a-modal.risk-warning > div > div > button')
        element.click()
        try:
            _element = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#listContent"))
            )
        except (TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException):
            self.driver.quit()
            print("此路不通")
        time.sleep(3)
        print(self.driver.current_url)
        container_elements = self.driver.find_elements_by_xpath(
            "//div[@class='contentpile__content__wrapper__item clearfix']")
        for container_element in container_elements:
            job_title = container_element.find_element_by_xpath(
                "//span[@class='contentpile__content__wrapper__item__info__box__jobname__title']//@title")
            print(job_title)
            location = container_element.find_element_by_xpath(
                "//li[1][@class='contentpile__content__wrapper__item__info__box__job__demand__item']")
            print(location)
            company_name = container_element.find_element_by_xpath(
                "//a[@class='contentpile__content__wrapper__item__info__box__cname__title company_title']//@title")
            company_url = container_element.find_element_by_xpath(
                "//a[@class='contentpile__content__wrapper__item__info__box__cname__title company_title']//@href")
            company_in_db = self.mydb.getByCompanyName(company_name)
            if company_in_db is None:
                company_obj = company.company(job_title, company_name, company_url, location)
                self.email_content = self.email_content + company_name + " " + company_url + '\r\n'
                self.mydb.save_company(company_obj)
            else:
                logging.info("Found existing record, hence quite.")
                raise CloseSpider("There's no new record yet.")
    def spider_closed(self, spider):
        self.mydb.close()
        self.driver.close()


