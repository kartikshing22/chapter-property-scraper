import scrapy
import json
import requests
from faker import Faker
from scrapy.selector import Selector
from ..items import BookingscraperItem
from .config import key, EMAIL_PASS, EMAIL_USER
from .proxy_api import ScraperAPIClient
import smtplib
from email.message import EmailMessage


class PropertySpider(scrapy.Spider):
    name = "property"

    def __init__(self, *args, **kwargs):
        super(PropertySpider, self).__init__(*args, **kwargs)
        self.prop_name = ""
        self.post_data = {
            "SiteId": "",
            "SiteTitle": "",
            "BookingPeriodId": [],
            "SortOption": "PriceAscending",
            "RoomTypes": [],
            "Prices": [],
            "RoomTiers": [],
            "NoResultsTitle": "No results found",
            "NoResultsText": "There were no rooms matching your preferences.",
        }
        self.handle_httpstatus_list = [400, 401, 403, 404, 500]

        self.main_form_data = {}
        self.lease = ""

        # Room type and there ids are fixed, so hardcoded
        self.floor_plan = {
            "Studio": "1166879",
            "Ensuite": "1166878",
            "Twin Studio": "1175818",
            "Two Bed Apartment": "1166854",
            "Twin Ensuite": "1175823",
        }

        # Room tier and there ids are fixed, so hardcoded
        self.space_options = {
            "Silver": "453",
            "Bronze": "454",
            "Gold": "458",
            "Platinum": "455",
            "Diamond": "456",
        }

    def start_requests(self):
        urls = ["https://www.chapter-living.com/booking/"]
        # response.status==200

        client = ScraperAPIClient(key)
        for url in urls:
            yield scrapy.Request(
                client.scrapyGet(url=url), callback=self.parse
            )  # using paid proxy which will provide different ip address everytime

    def parse(self, response):
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)

        options = response.css("#BookingAvailabilityForm_Residence option")
        form = response.css("#BookingAvailabilityForm")

        for input_tag in form.css("input"):
            name = input_tag.xpath("@name").get()
            value = input_tag.xpath("@value").get()
            self.main_form_data[name] = value

        self.log(self.main_form_data)

        for option in options:  # getting all the properties id and name
            property_id = option.css("::attr(value)").get()
            property_name = option.css("::text").get()
            if (
                "CHAPTER KINGS CROSS" in property_name
            ):  # scraping data only for CHAPTER KINGS CROSS
                self.post_data["SiteId"] = property_id
                self.post_data["SiteTitle"] = property_name
                self.main_form_data["Residence"] = property_id
                self.prop_name = "CHAPTER KINGS CROSS"

        yield scrapy.FormRequest(
            url="https://www.chapter-living.com/umbraco/surface/BookingAvailabilitySurface/UpdateFormRoomListView",
            formdata=self.post_data,
            callback=self.parse_booking_period_page,
            errback=self.error_logger,
        )

    def parse_booking_period_page(self, response):
        # getting the duration of property
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)

        booking_period = "https://www.chapter-living.com/umbraco/surface/BookingAvailabilitySurface/UpdateBookingPeriods"
        formdata = {"siteId": self.post_data["SiteId"]}
        peroid_response = requests.post(booking_period, data=formdata)
        periods = json.loads(peroid_response.text)

        for period in periods:
            if period["Text"] == "SEP 24 - AUG 25 (51 WEEKS)":
                self.post_data["BookingPeriodId"] = period["Value"]
                self.main_form_data["BookingPeriod"] = period["Value"]
        self.post_data["RoomTypes"] = "Ensuite"

        url = "https://www.chapter-living.com/umbraco/surface/BookingAvailabilitySurface/UpdateFormRoomListView"

        yield scrapy.FormRequest(
            url=url,
            formdata=self.post_data,
            callback=self.required_login_detail,
            errback=self.error_logger,
        )

    def required_login_detail(self, response):

        # creating the form and passing to the url which will redirect to login page
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)
        self.images = response.css(
            'source[srcset*="width=2000"][srcset*="height=1000"]::attr(srcset)'
        ).getall()
        self.property_name = response.css("p.property::text").get()
        self.room_type = response.css("p.display-4 strong::text").get()
        self.description = response.css("div.description p::text").getall()
        self.pricing = response.css("p.pricing strong::text").get()
        self.features = response.css("ul.features-list li::text").getall()

        floorplan_element = response.css("div#modal-room-1.sp-room")
        if floorplan_element:
            floorplan_id = floorplan_element.attrib.get("data-floorplanid")
            space_configuration = floorplan_element.attrib.get(
                "data-spaceconfiguration"
            )
            self.main_form_data["FloorPlan"] = floorplan_id
            self.main_form_data["SpaceConfiguration"] = space_configuration
            self.main_form_data["BookingUrl"] = response.css(
                "a.btn.btn-black.room-list-selection::attr(href)"
            ).extract_first()

            form_data = {
                "__RequestVerificationToken": self.main_form_data[
                    "__RequestVerificationToken"
                ],
                "ResultsPlaceholderTitle": self.main_form_data[
                    "ResultsPlaceholderTitle"
                ],
                "ResultsPlaceholderText": self.main_form_data["ResultsPlaceholderText"],
                "NoResultsTitle": self.main_form_data["NoResultsTitle"],
                "NoResultsText": self.main_form_data["NoResultsText"],
                "FloorPlan": self.main_form_data["FloorPlan"],
                "SpaceConfiguration": self.main_form_data["SpaceConfiguration"],
                "Residence": self.main_form_data["Residence"],
                "BookingPeriod": self.main_form_data["BookingPeriod"],
                "SortOption": "PriceAscending",
                "University": "",
                "ufprt": self.main_form_data["ufprt"],
            }

            pid, lease_id, floor_plan_id = (
                form_data["Residence"],
                form_data["BookingPeriod"],
                form_data["FloorPlan"],
            )
            self.property_link_name = self.property_name.lower().replace(
                " ", ""
            )  #'chapterkingscross'
            url = f"https://{self.property_link_name}.prospectportal.global/Apartments/module/application_authentication/property[id]/{pid}/property_floorplan[id]/{floor_plan_id}/lease_term_id/{lease_id}/lease_start_window_id/180434/space_configuration_id/454/from_check_availability/1"

            yield scrapy.FormRequest(
                url=url,
                formdata=form_data,
                method="GET",
                callback=self.login_page,
                errback=self.error_logger,
            )

    def login_page(self, response):
        # filling the signup page with fake details and loggingin
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)

        application_id = response.xpath(
            '//li[@class="is-hidden"]/input[@name="application[company_application_id]"]/@value'
        ).get()
        fake = Faker()
        password = fake.password()
        lease_window = response.xpath(
            '//input[@name="application[lease_start_window_id]"]/@value'
        ).get()
        space_conf_id = response.xpath(
            '//input[@name="application[space_configuration_id]"]/@value'
        ).get()
        move_in = response.xpath(
            '//input[@name="application[desired_movein_date]"]/@value'
        ).get()
        term_month = response.xpath(
            '//input[@name="application[term_month]"]/@value'
        ).get()
        pid = self.main_form_data["Residence"]
        p_number = str(fake.random_number(digits=10))

        form_data = {
            "application[company_application_id]": application_id,
            "show_terms_and_conditions": "1",
            "show_privacy_policy": "0",
            "applicant[customer_relationship_id]": "1",
            "applicant[name_first]": fake.first_name(),
            "applicant[name_last]": fake.last_name(),
            "masked-phone_numbers[0][phone_number]-country": "+91",
            "masked-phone_numbers[0][phone_number]-base": p_number,
            "phone_numbers[0][phone_number]": "+91 " + p_number,
            "phone_numbers[0][phone_number_type]": "4",
            "phone_numbers[0][is_primary]": "on",
            "applicant[username]": fake.email(),
            "is_from_roommate_invitation": "",
            "applicant_username": "",
            "applicant_id": "",
            "applicant[password]": password,
            "applicant[password_confirm]": password,
            "agrees_to_terms": "1",
            "is_new_applicant": "1",
            "application_id": "",
            "application[term_month]": term_month,
            "application[desired_movein_date]": move_in,
            "application[property_floorplan_id]": self.main_form_data["FloorPlan"],
            "application[lease_term_id]": self.main_form_data["BookingPeriod"],
            "application[lease_start_window_id]": lease_window,
            "application[space_configuration_id]": space_conf_id,
            "selected_occupancy_type[id]": "",
            "from_check_availability": "1",
        }

        yield scrapy.FormRequest(
            url=f"https://{self.property_link_name}.prospectportal.global/Apartments/module/application_authentication/action/insert_applicant/property[id]/{pid}/from_check_availability/1",
            formdata=form_data,
            callback=self.after_login,
            errback=self.error_logger,
        )

    def after_login(self, response):
        # removing the filters
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)

        self.lease = response.xpath(
            '//input[@class="student_units_filter"]/@value'
        ).get()
        url = f"https://{self.property_link_name}.prospectportal.global/Apartments/module/application_unit_info/action/view_unit_spaces_for_student//is_ajax/1/selected_filter/reset/is_change_selection/1"
        yield scrapy.FormRequest(
            url=url,
            callback=self.reset_filters,
            errback=self.error_logger,
        )

    def reset_filters(self, response):
        # adding filter to select all the FLOOR PLANS
        url = f"https://{self.property_link_name}.prospectportal.global/Apartments/module/application_unit_info/action/view_unit_spaces_for_student//is_ajax/1/selected_filter/property_floorplan_ids"

        payload = {
            "student_units_filter[lease_start_window_id]": "",
            "lease_start_window_ids": "|".join(self.lease),
            "student_units_filter[property_floorplan_ids]": ",".join(
                self.floor_plan.values()
            ),
            "all_floorplan_ids": "|".join(self.floor_plan.values()),
            "all_floorplan_names": "|".join(self.floor_plan.keys()),
            "student_units_filter[space_configuration_ids]": "",
            "student_units_filter[min_rent]": "",
            "student_units_filter[max_rent]": "",
            "student_units_filter[rent_range][min]": "315.00",
            "student_units_filter[rent_range][max]": "1249.00",
            "student_units_filter[number_of_bedrooms]": "",
            "student_units_filter[number_of_bathrooms]": "",
            "student_units_filter[property_floor_ids]": "",
            "student_units_filter[selected_floor_numbers]": "",
            "student_units_filter[gender_id]": "",
            "student_units_filter[unit_occupancy_status]": "",
            "is_change_selection": "1",
        }

        yield scrapy.FormRequest(
            url=url,
            formdata=payload,
            callback=self.property_floorplan_filters,
            errback=self.error_logger,
        )

    def property_floorplan_filters(self, response):
        # adding filter to select all the SPACE OPTION
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)

        url = f"https://{self.property_link_name}.prospectportal.global/Apartments/module/application_unit_info/action/view_unit_spaces_for_student//is_ajax/1/selected_filter/space_configuration_ids"

        payload = {
            "student_units_filter[lease_start_window_id]": "",
            "lease_start_window_ids": "|".join(self.lease),
            "lease_start_window_ids": "|".join(self.lease),
            "student_units_filter[property_floorplan_ids]": ",".join(
                self.floor_plan.values()
            ),
            "all_floorplan_ids": "|".join(self.floor_plan.values()),
            "all_floorplan_names": "|".join(self.floor_plan.keys()),
            "student_units_filter[space_configuration_ids]": ",".join(
                self.space_options.values()
            ),
            "student_units_filter[min_rent]": "",
            "student_units_filter[max_rent]": "",
            "student_units_filter[rent_range][min]": "315.00",
            "student_units_filter[rent_range][max]": "1249.00",
            "student_units_filter[number_of_bedrooms]": "",
            "student_units_filter[number_of_bathrooms]": "",
            "student_units_filter[property_floor_ids]": "",
            "student_units_filter[selected_floor_numbers]": "",
            "student_units_filter[gender_id]": "",
            "student_units_filter[unit_occupancy_status]": "",
            "is_change_selection": "1",
        }

        yield scrapy.FormRequest(
            url=url,
            formdata=payload,
            callback=self.space_configuration_filters,
            errback=self.error_logger,
        )

    def space_configuration_filters(self, response):

        # Getting the data of property and sending to mongodb
        if response.status in self.handle_httpstatus_list:
            yield scrapy(callback=self.error_logger)

        item = BookingscraperItem()

        final_data = {}
        final_data[self.prop_name] = []
        cards = response.css(".floorplan-card ").getall()
        for count, i in enumerate(cards):
            element = {}
            selector = Selector(text=i)
            image_src = selector.css(".floorplan-image img::attr(src)").get()
            floorplan_name = selector.css(".floorplan-name::text").get()
            price = selector.css(".price-bar span::text").get()
            bed_bath_info = selector.css(".price-bar span:nth-child(2)::text").get()
            amenities = selector.css(".pad15-top .containers span::text").getall()
            lease_terms = selector.css(
                ".pad15-top .table_load_pricing td:first-child::text"
            ).getall()
            pricing = selector.css(
                ".pad15-top .table_load_pricing td:nth-child(2)::text"
            ).getall()

            element["id"] = count
            element["image"] = image_src
            element["price"] = price
            element["bed_bath_info"] = bed_bath_info
            element["amenities"] = amenities
            element["lease_terms"] = lease_terms
            element["pricing"] = pricing
            element["floorplan_name"] = floorplan_name
            final_data[self.prop_name].append(element)
        item["property_name"] = self.prop_name
        item["sub_properties"] = final_data[self.prop_name]
        item["property_images"] = self.images
        item["property_room_type"] = self.room_type
        item["property_description"] = self.description
        item["property_price"] = self.pricing
        item["property_features"] = self.features

        yield item

    def error_logger(self, response):
        # Script to send the Failed url details to mail
        msg = EmailMessage()
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER
        msg["Subject"] = "Failed Url and Stoped Scraper"
        msg.set_content(
            f"The scraper has been stopped for url {response.request._url}, Please check the issue and re run script"
        )

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        # any another script which will re run the scraper from following URL or send mail

        item = BookingscraperItem()

        item["url"] = response.request._url
        item["is_failed"] = "true"
        item["error"] = str(response.getErrorMessage)
        yield item
