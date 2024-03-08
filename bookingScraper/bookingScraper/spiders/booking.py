import scrapy
import json
import requests
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
from .config import key
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.chrome.service import Service


class BookingSpider(scrapy.Spider):
    name = "booking"
    allowed_domains = ["www.chapter-living.com"]
    start_urls = ["https://www.chapter-living.com/booking/"]

    def __init__(self, *args, **kwargs):
        super(BookingSpider, self).__init__(*args, **kwargs)
        service = Service(executable_path="./chromedriver.exe")
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=service, options=options)
        # self.driver = webdriver.Chrome()

    def start_requests(self):
        urls = ["https://www.chapter-living.com/booking/"]
        for url in urls:
            # yield scrapy.Request(url=url, callback=self.parse)
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                meta={
                    "proxy": "http://scraperapi:{}@proxy-server.scraperapi.com:8001".format(
                        key
                    ),
                    "proxy_type": "http",  # Specify the proxy type
                },
            )

    def parse(self, response):
        # self.driver.get("https://www.chapter-living.com/booking/")
        # headlines = driver.find_elements_by_class_name("property")
        property_dropdown = self.driver.find_element(
            By.ID, "BookingAvailabilityForm_Residence"
        )

        property_dropdown_select = Select(property_dropdown)
        property_dropdown_select.select_by_visible_text("CHAPTER KINGS CROSS")

        duration_dropdown = self.driver.find_element(
            By.ID, "BookingAvailabilityForm_BookingPeriod"
        )
        print(duration_dropdown.text)

        # Perform other interactions or extractions using Selenium

        self.driver.close()
