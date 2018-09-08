# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json, codecs
import pymysql
from twisted.enterprise import adbapi

class LianjiaPipeline(object):

    @classmethod
    def from_settings(cls,settings):
        dbparms = settings.get("MYSQL_CONNECT")
        dbpool = adbapi.ConnectionPool("pymysql",**dbparms)
        return cls(dbpool)

    def __init__(self,dbpool):
        self.dbpool = dbpool

    def __del__(self):
        self.dbpool.close()

    def open_spider(self, spider):

        query = self.dbpool.runInteraction(self.update_house_ids, spider)
        query.addErrback(self.handle_error)

    def update_house_ids(self, cursor, spider):

        exist_house_sql = '''select id from lj_house'''
        cursor.execute(exist_house_sql)
        result = cursor.fetchall()
        if result:
            # 使用house[0]取出数据，因为result的子项是tuple类型
            spider.exist_house_ids = set([str(house[0]) for house in result])
        else:
            # 设置已存储的house列表
            spider.exist_house_ids = set()

    def handle_error(self,failure):
        #处理数据库异常
        print(failure)

    def process_item(self, item, spider):

        if item.get('layer') is None:
            item['layer'] = '暂无数据'
        if item.get('structure') is None:
            item['structure'] = '试试看吧'

        return item

class JsonWithEncodingPipeline(object):

    def open_spider(self, spider):
        self.file = codecs.open("lianjia.json",'w',encoding="utf-8")

    def close_spider(self,spider):
        self.file.close()

    def process_item(self, item, spider):

        url = json.dumps(str(item['url']),ensure_ascii=False) + "\n"
        xiaoqu = json.dumps("小区：" + str(item['xiaoqu']),ensure_ascii=False) + "\n"
        huxing = json.dumps("户型：" + str(item['huxing']),ensure_ascii=False) + "\n"
        mianji = json.dumps("面积：" + str(item['mianji']),ensure_ascii=False) + "\n"
        chaoxiang = json.dumps("朝向：" + str(item['chaoxiang']),ensure_ascii=False) + "\n"
        zhuangxiu = json.dumps("装修：" + str(item['zhuangxiu']),ensure_ascii=False) + "\n"
        line = url + xiaoqu + huxing + mianji + chaoxiang + zhuangxiu
        self.file.write(line)

        louceng = json.dumps("楼层：" + str(item['floor']),ensure_ascii=False) + "\n"
        lougao = json.dumps("楼高：" + str(item['total_floor']), ensure_ascii=False) + "\n"
        jiancheng = json.dumps("建成：" + str(item['built_year']),ensure_ascii=False) + "\n"
        leixing = json.dumps("类型：" + str(item['structure']),ensure_ascii=False) + "\n"
        quyu = json.dumps("区域：" + str(item['region']),ensure_ascii=False) + "\n"
        line = louceng + lougao + jiancheng + leixing + quyu
        self.file.write(line)

        guanzhu = json.dumps("关注：" + str(item['follow']),ensure_ascii=False) + "\n"
        daikan = json.dumps("带看：" + str(item['visit']),ensure_ascii=False) + "\n"
        tag = json.dumps("标签：" + str(item['tags']),ensure_ascii=False) + "\n"
        price = json.dumps("总价：" + str(item['price']) + " 万",ensure_ascii=False) + "\n"
        unitPrice = json.dumps("单价：" + str(item['unit_price']) + " 元/平米",ensure_ascii=False) + "\n"
        line = guanzhu + daikan + tag + price + unitPrice
        self.file.write(line)

        self.file.write("\n")
        return item


class MysqlTwistedPipline(object):
    '''
    采用异步的方式插入数据
    '''
    @classmethod
    def from_settings(cls,settings):
        dbparms = settings.get("MYSQL_CONNECT")
        dbpool = adbapi.ConnectionPool("pymysql",**dbparms)
        return cls(dbpool)

    def __init__(self,dbpool):
        self.dbpool = dbpool

    def __del__(self):
        self.dbpool.close()

    def process_item(self,item,spider):
        '''
        使用twisted将mysql插入变成异步
        :param item:
        :param spider:
        :return:
        '''
        query = self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error)

    def handle_error(self,failure):
        #处理异步插入的异常
        print(failure)

    def do_insert(self,cursor,item):
        #具体插入数据
        insert_house_sql = '''
            insert into lj_house
            ( id, 
            community, region,
            type, area, orientation, 
            decoration, layer, heating,
            floor, total_floor, built_year, structure,
            tags, url,
            crawl_time) 
            VALUES (%s,
            %s,%s,
            %s,%s,%s,
            %s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,
            %s)
            ON DUPLICATE KEY UPDATE
            crawl_time=VALUES(crawl_time)
            '''
        insert_price_sql = '''
            insert into lj_house_price
            ( id, 
            price, unit_price,
            crawl_time) 
            VALUES (%s,
            %s,%s,
            %s)
            '''
        insert_follow_sql = '''
            insert into lj_house_follow
            ( id, 
            follow, visit,
            crawl_time) 
            VALUES (%s,
            %s,%s,
            %s)
            '''

        cursor.execute(insert_house_sql,
                       (item['hid'], 
                        item['xiaoqu'], item['region'],
                        item['huxing'], item['mianji'], item['chaoxiang'], 
                        item['zhuangxiu'], item['layer'], item['heating'],
                        item['floor'], item['total_floor'],
                        item['built_year'], item['structure'],
                        item['tags'], item['url'],
                        item['crawl_time']
                    ))
        cursor.execute(insert_price_sql,
                       (item['hid'], 
                        item['price'], item['unit_price'],
                        item['crawl_time']
                    ))
        cursor.execute(insert_follow_sql,
                       (item['hid'], 
                        item['follow'], item['visit'],
                        item['crawl_time']
                    ))
