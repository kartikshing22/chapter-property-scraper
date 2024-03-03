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


class BookingSpider(scrapy.Spider):
    name = "booking"
    allowed_domains = ["www.chapter-living.com"]
    start_urls = ["https://www.chapter-living.com/booking/"]

    def __init__(self, *args, **kwargs):
        super(BookingSpider, self).__init__(*args, **kwargs)
        self.driver = webdriver.Chrome()

    def start_requests(self):
        urls = ["https://www.chapter-living.com/booking/"]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.driver.get("https://www.chapter-living.com/booking/")
        # headlines = driver.find_elements_by_class_name("property")
        property_dropdown = self.driver.find_element(
            By.ID, "BookingAvailabilityForm_Residence"
        )

        property_dropdown_select = Select(property_dropdown)
        property_dropdown_select.select_by_visible_text("CHAPTER KINGS CROSS")
        time.sleep(1)
        duration_dropdown = self.driver.find_element(
            By.ID, "BookingAvailabilityForm_BookingPeriod"
        )

        duration_dropdown_select = Select(property_dropdown)
        duration_dropdown_select.select_by_visible_text("SEP 24 - AUG 25 (51 WEEKS)")
        ensuite_checkbox = self.driver.find_element(By.ID, "filter-room-type-ensuite")
        ensuite_checkbox.click()
        apply_button = self.driver.find_element(
            By.CSS_SELECTOR, "a.btn.btn-black.room-list-selection"
        )
        apply_button.click()

        time.sleep(10)

        # for headline in headlines:
        #     print("kartik===============", headline.text)
        self.driver.close()
