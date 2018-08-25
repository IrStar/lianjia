# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LianjiaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    hid = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    
    follow = scrapy.Field()
    visit = scrapy.Field()
    tags = scrapy.Field()
    
    crawl_time = scrapy.Field()
    
    price = scrapy.Field()
    unit_price = scrapy.Field()

    huxing = scrapy.Field()
    floor = scrapy.Field()
    total_floor = scrapy.Field()
    chaoxiang = scrapy.Field()
    layer = scrapy.Field()
    zhuangxiu = scrapy.Field()
    heating = scrapy.Field()
    mianji = scrapy.Field()
    built_year = scrapy.Field()
    structure = scrapy.Field()

    xiaoqu = scrapy.Field()
    region = scrapy.Field()

    pass

class DmozItem(scrapy.Item):
    title = scrapy.Field()
    time = scrapy.Field()
    desc = scrapy.Field()
    url = scrapy.Field()