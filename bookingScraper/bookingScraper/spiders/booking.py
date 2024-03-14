import scrapy
from faker import Faker
from selenium import webdriver
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
from faker import Faker
from ..items import BookingscraperItem
from .config import key
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.common.by import By


class BookingSpider(scrapy.Spider):
    name = "booking"
    allowed_domains = ["www.chapter-living.com"]
    start_urls = ["https://www.chapter-living.com/booking/"]

    def __init__(self, *args, **kwargs):
        super(BookingSpider, self).__init__(*args, **kwargs)
        service = Service(executable_path="./chromedriver.exe")
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=service, options=options)

    def start_requests(self):
        urls = ["https://www.chapter-living.com/booking/"]
        for url in urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
            )

    def parse(self, response):
        self.driver.get("https://www.chapter-living.com/booking/")
        property_to_be_scraped = "CHAPTER KINGS CROSS"  # "CHAPTER KINGS CROSS"
        property_tenure = "SEP 24 - AUG 25 (51 WEEKS)"  # "SEP 24 - AUG 25 (51 WEEKS)"
        property_dropdown = self.driver.find_element(
            By.ID, "BookingAvailabilityForm_Residence"
        )
        self.driver.find_element(By.ID, "onetrust-reject-all-handler").click()

        # Selecting Property
        property_dropdown_select = Select(property_dropdown)
        property_dropdown_select.select_by_visible_text(property_to_be_scraped)
        time.sleep(10)

        # Selecting the booking period tenure
        duration_dropdown = self.driver.find_element(
            By.ID, "BookingAvailabilityForm_BookingPeriod"
        )
        property_dropdown_select = Select(duration_dropdown)
        property_dropdown_select.select_by_visible_text(property_tenure)
        time.sleep(10)

        # Seleting filter for Ensuite type
        checkbox = self.driver.find_element(By.ID, "filter-room-type-ensuite")
        checkbox.click()
        time.sleep(3)

        try:
            # fetching images and other details of property, fetching only for 1st property
            main_card_details = self.driver.page_source
            main_card_details = Selector(text=main_card_details)
            main_cards = main_card_details.response.css("div.sp-room")
            if main_cards[0]:
                card = main_cards[0]
                property_images = card.css(
                    'source[srcset*="width=2000"][srcset*="height=1000"]::attr(srcset)'
                ).getall()
                property_name = card.css("p.property::text").get()
                room_type = card.css("p.display-4 strong::text").get()
                price_range = card.css("p.pricing strong::text").get()
                features = card.css("ul.features-list li::text").getall()
            # for card in main_cards:
            #     property_images = card.css(
            #         'source[srcset*="width=2000"][srcset*="height=1000"]::attr(srcset)'
            #     ).getall()
            #     property_name = card.css("p.property::text").get()
            #     room_type = card.css("p.display-4 strong::text").get()
            #     price_range = card.css("p.pricing strong::text").get()
            #     features = card.css("ul.features-list li::text").getall()
        except:
            property_images = ""
            property_name = ""
            room_type = ""
            price_range = ""
            features = ""

        time.sleep(5)
        self.driver.find_element(By.CLASS_NAME, "room-list-selection").click()

        time.sleep(5)
        self.driver.find_element(By.ID, "pc_banner_reject_all").click()
        time.sleep(4)

        # Filling the SignupUp from using faker
        fake = Faker()
        password = fake.password()
        self.driver.find_element(By.ID, "applicant_first_name").send_keys(
            fake.first_name()
        )
        self.driver.find_element(By.ID, "applicant_last_name").send_keys(
            fake.last_name()
        )
        self.driver.find_element(By.CLASS_NAME, "country-code ").clear()
        self.driver.find_element(By.CLASS_NAME, "country-code ").send_keys("91")
        self.driver.find_element(By.CLASS_NAME, "phone-number").send_keys(
            str(fake.random_number(digits=10))
        )

        self.driver.find_element("xpath", "//input[@type='email']").send_keys(
            fake.email()
        )

        self.driver.find_element(By.ID, "applicant_password").send_keys(password)
        self.driver.find_element(By.NAME, "applicant[password]").send_keys(password)
        self.driver.find_element(By.NAME, "applicant[password_confirm]").send_keys(
            password
        )
        self.driver.find_element(By.ID, "is_primary_0").click()
        self.driver.find_element(By.ID, "agrees_to_terms").click()
        self.driver.find_element(By.ID, "create-app-btn").click()
        time.sleep(2)
        self.driver.find_element(By.CLASS_NAME, "js-confirm").click()
        time.sleep(18)  # form has been submited and redirected property details

        # reseting the filters
        self.driver.find_element(By.CLASS_NAME, "reset-filters").click()
        time.sleep(10)

        # fetching all unique details of properties varients
        cards_html = self.driver.page_source
        selector = Selector(text=cards_html)
        floorplan_cards = selector.css(".floorplan-card").getall()
        cards_id = []
        for card in floorplan_cards:
            card_selector = Selector(text=card)
            data = {
                "data_property_id": card_selector.xpath(".//@data-property_id").get(),
                "data_property_floorplan_id": card_selector.xpath(
                    ".//@data-property_floorplan_id"
                ).get(),
                "data_space_configuration_id": card_selector.xpath(
                    ".//@data-space_configuration_id"
                ).get(),
            }
            cards_id.append(data)

        # first loops starts here
        property_dump = {"sub_properties": []}

        # looping on all the property varient to fetch the varients data
        for i in range(len(cards_id)):  #
            i = cards_id[i]
            xpath = f"//input[@data-property_id={i['data_property_id']} and @data-property_floorplan_id={i['data_property_floorplan_id']} and @data-space_configuration_id={i['data_space_configuration_id']}]"
            time.sleep(3)
            self.driver.find_element("xpath", xpath).click()
            time.sleep(5)
            li = self.driver.find_elements(
                By.CSS_SELECTOR, "ul.lease-term-ul li.lease-term-list"
            )
            tenures = [element.get_attribute("id") for element in li]
            tenure_wise_data = {"tenures": []}

            # looping to all tenures of a varient, as we require availablty of room by tenure and scraping all the details, this is the main loop where we are getting all required data
            try:
                for j in range(len(tenures)):
                    tenure_obj = tenures[j]
                    try:
                        self.driver.find_element(
                            By.ID, tenure_obj
                        ).click()  # change this
                    except:
                        self.driver.refresh()
                        time.sleep(8)
                        self.driver.find_element(By.CLASS_NAME, "reset-filters").click()
                        time.sleep(8)
                        self.driver.find_element("xpath", xpath).click()
                        time.sleep(8)
                        self.driver.find_element(By.ID, tenure_obj).click()

                    time.sleep(10)
                    final_data = self.driver.page_source
                    final_data_selector = Selector(text=final_data)
                    property_varient_name = self.driver.find_element(
                        By.CLASS_NAME, "floorplan-space-name"
                    ).text.strip()  # include
                    propert_varient_img = self.driver.find_elements(
                        By.CSS_SELECTOR, ".image-container img"
                    )
                    propert_varient_img = [
                        element.get_attribute("src") for element in propert_varient_img
                    ]  # include
                    try:
                        tenure_duration = (
                            final_data_selector.css(
                                ".sus-unit-details h6:first-of-type::text"
                            )
                            .extract_first()
                            .strip()
                        )
                    except:
                        tenure_duration = ""
                    try:
                        final_cards = final_data_selector.css(
                            ".sus-unit-space-details"
                        ).getall()
                    except:
                        final_cards = None
                    unit_spaces_cards = []
                    unit_info = {}
                    unit_info["property_varient_name"] = property_varient_name
                    unit_info["propert_varient_img"] = propert_varient_img
                    unit_info["tenure_period"] = tenure_duration  # change this

                    # one property varient have multiple rooms, fetching the varients room data
                    if final_cards:
                        for availabilty in final_cards:
                            availabilty = Selector(text=availabilty)
                            try:
                                building_number = availabilty.css(
                                    ".sus-unit-space-details h6::text"
                                ).get()
                            except:
                                pass
                            rent = availabilty.css(
                                '.title:contains("Rent") + .value::text'
                            ).get()
                            building = availabilty.css(
                                '.title:contains("Building") + .value::text'
                            ).get()
                            deposit = availabilty.css(
                                '.title:contains("Deposit") + .value::text'
                            ).get()
                            amenities = availabilty.css(
                                '.title:contains("Amenities") + .value::text'
                            ).get()
                            unit_spaces = []
                            for tr in availabilty.css(".unit-space-table tbody tr"):
                                space = tr.css("td:nth-child(2)::text").get().strip()
                                status = tr.css("td:nth-child(3)::text").get().strip()
                                unit_spaces.append({"space": space, "status": status})
                            payment_plan_options = []
                            for li in availabilty.css(
                                ".payment-option-container .radio-group-list li"
                            ):
                                plan_name = li.css("span.value::text").get()
                                payment_plan_options.append(plan_name)
                            units = {
                                "builder_number": building_number,
                                "building": building,
                                "rent": rent,
                                "deposit": deposit,
                                "amenities": amenities,
                                "unit_spaces": unit_spaces,
                                "payment_plan_options": payment_plan_options,
                            }
                            unit_spaces_cards.append(units)
                        if unit_spaces_cards:
                            unit_info["unit_space_details"] = unit_spaces_cards
                        if tenure_wise_data["tenures"] != None:
                            if unit_info not in tenure_wise_data["tenures"]:
                                tenure_wise_data["tenures"].append(unit_info)

                        else:
                            tenure_wise_data["tenures"] = [unit_info]
                        tenure_wise_data["property_varient_name"] = unit_info[
                            "property_varient_name"
                        ]
                        tenure_wise_data["propert_varient_img"] = unit_info[
                            "propert_varient_img"
                        ]

                    # To handle the failed cases, below click are required , after fetch one varient data , reseting filters clicking on the property varient
                    self.driver.find_element(By.CLASS_NAME, "reset-filters").click()
                    time.sleep(8)

                    if j != len(tenures) - 1:
                        self.driver.find_element("xpath", xpath).click()
                        time.sleep(8)
            except:
                pass
            if property_dump["sub_properties"] != None:
                property_dump["sub_properties"].append(tenure_wise_data)
            else:
                property_dump["sub_properties"] = [tenure_wise_data]

        # Created a Pipeline of items which will take the data to mongodb
        import datetime

        item = BookingscraperItem()
        item["sub_properties"] = property_dump["sub_properties"]
        item["property_name"] = property_name
        item["property_images"] = property_images
        item["property_room_type"] = room_type
        item["property_price"] = price_range
        item["property_features"] = features
        item["created_at"] = datetime.datetime.now()

        self.driver.close()
        yield item
