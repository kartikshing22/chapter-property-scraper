# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookingscraperItem(scrapy.Item):
    property_name = scrapy.Field()
    sub_properties = scrapy.Field()
