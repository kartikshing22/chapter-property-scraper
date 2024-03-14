# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookingscraperItem(scrapy.Item):
    is_failed = scrapy.Field()
    url = scrapy.Field()
    error = scrapy.Field()
    property_name = scrapy.Field()
    sub_properties = scrapy.Field()
    property_images = scrapy.Field()
    property_room_type = scrapy.Field()
    property_description = scrapy.Field()
    property_price = scrapy.Field()
    property_features = scrapy.Field()
    created_at = scrapy.Field()
