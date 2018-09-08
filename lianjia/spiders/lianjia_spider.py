#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 19 22:36:30 2018

@author: tongq
"""

import scrapy
from bs4 import BeautifulSoup
from datetime import datetime

from lianjia.items import LianjiaItem

count_houses = 0
class LianjiaSpider(scrapy.Spider):
    name = "lianjia"
    allowed_domains = ["bj.lianjia.com", "lf.lianjia.com"]
    start_urls = [
#            "http://bj.lianjia.com/ershoufang/hy1bt1y2ea1000ep1000/", # 集体供暖，塔楼，10年以内，1000平以内，1000w以内
#            "http://bj.lianjia.com/ershoufang/hy1bt2y2ea1000ep1000/", # 同上，板楼
#            "http://bj.lianjia.com/ershoufang/hy1bt3y2ea1000ep1000/", # 同上，板塔结合
#            "http://bj.lianjia.com/ershoufang/hy2y2ea1000ep1000/"     # 同上，自供暖
            "https://bj.lianjia.com/ershoufang/hy2y2ba250ea1000bp900ep1000/"
            ]

    house_ids = []

    def parse(self, response):
        global count_houses

        soup = BeautifulSoup(response.text, 'lxml')

        houses = soup.find_all('div', 'info clear')
        count_houses += len(houses)
        print("\n********************")
        print("Current Houses: ", count_houses)
        print("********************\n")

        for house in houses:
            houseItem = LianjiaItem()

            # 唯一编号、url、标题
            url = house.find('div', 'title')
            houseItem['hid'] = url.a['href'].split('/')[-1][:-5]
            houseItem['url'] = url.a['href']
            houseItem['crawl_time'] = datetime.now()

            # 关注与带看
            followInfo = house.find('div', 'followInfo')
            houseItem['follow'] = followInfo.contents[0].string[0:-3]
            daikan = followInfo.find('span', 'divide').next_sibling.string
            houseItem['visit'] = daikan[0:-3]

            # 房屋售价
            priceInfo = house.find('div', 'priceInfo')
            houseItem['price'] = priceInfo.find('div','totalPrice').span.string
            houseItem['unit_price'] = priceInfo.find('div','unitPrice').span.string[2:-4]

            # 房屋标签
            tags = followInfo.find('div', 'tag')
            tag_content = ''
            tag_details = tags.find_all('span')
            for tag in tag_details:
                tag_content = tag_content + tag.string + ','
            if len(tag_content) > 0 and tag_content[-1] == ',':
                tag_content = tag_content[:-1]
            houseItem['tags'] = tag_content

            # 若该房屋已经存在于数据库中，则无需读取房屋详情
            if houseItem['hid'] in self.exist_house_ids:
                yield houseItem
                continue

            # 获取详细信息
            houseItem['title'] = url.a.string
            yield scrapy.Request(url=houseItem['url'], meta={'item':houseItem}, 
                                 callback = self.parse_detail)

        # 总页数与当前页
        page_box = soup.find('div', 'page-box house-lst-page-box')
        page_data = page_box['page-data'][1:-1]
        totalPage = 0
        curPage = 0
        for pi in page_data.split(','):
            if pi.find('totalPage') > 0:
                totalPage = int(pi[pi.find('totalPage')+11:])
            elif pi.find('curPage') > 0:
                curPage = int(pi[pi.find('curPage')+9:])

        print("CurPage: {}, TotalPage: {}".format(curPage, totalPage))
        # 未到达最后一页，则翻页
        if curPage < totalPage and curPage < 100:
            page_url = page_box['page-url']
            next_page_url = response.urljoin(page_url.replace('{page}',str(curPage+1)))
            print("Next page URL: {}".format(next_page_url))
#        next_page = pages_url.contents[-1]
#        if next_page is not None and pages < 2:
#            next_page_url = response.urljoin(next_page['href'])
            yield scrapy.Request(url=next_page_url, callback=self.parse)


    def parse_detail(self, response):
        houseItem = response.meta['item']
        print("House ID: " + str(houseItem['hid']) + "\t" + str(houseItem['title']))

        soup = BeautifulSoup(response.text, 'lxml')

        # 若房屋为车位，则跳过
        if soup.find('div', 'houseInfo').find('div', 'room').find('div', 'mainInfo').string == '车位':
            return None

        # 房屋面积，建成年份
        areaInfo = soup.find('div', 'houseInfo').find('div', 'area')
        houseItem['mianji'] = areaInfo.find('div', 'mainInfo').string[:-2] # 93.71
        niandai = areaInfo.find('div', 'subInfo').string.split('/')
        houseItem['built_year'] = niandai[0][:-2] # 2010

        # 房屋各项信息
        info = soup.find('div', 'm-content').find('div', 'introContent').find('div', 'base').find('div', 'content').find_all('li')
        for li in info:
            if li.span.text == '房屋户型':
                houseItem['huxing'] = li.get_text()[4:]
            elif li.span.text == '所在楼层':
                louceng = ''.join(li.get_text()[4:].split()).split('(')
                houseItem['floor'] = louceng[0]
                houseItem['total_floor'] = louceng[1][1:-2]
            elif li.span.text == '户型结构':
                houseItem['layer'] = li.get_text()[4:]
            elif li.span.text == '建筑类型':
                houseItem['structure'] = li.get_text()[4:]
            elif li.span.text == '房屋朝向':
                houseItem['chaoxiang'] = li.get_text()[4:].replace(' ', ',')
            elif li.span.text == '装修情况':
                houseItem['zhuangxiu'] = li.get_text()[4:]
            elif li.span.text == '供暖方式':
                houseItem['heating'] = li.get_text()[4:]

        # 房屋区域信息
        aroundInfo = soup.find('div', 'aroundInfo')
        communityName = aroundInfo.find('div', 'communityName')
        houseItem['xiaoqu'] = communityName.find('a', 'info').string
        areaName = aroundInfo.find('div', 'areaName')
        region = areaName.find('span', 'info').get_text() + ' ' + areaName.find('a', 'supplement').get_text()
        houseItem['region'] = ','.join(region.split())

        yield houseItem
