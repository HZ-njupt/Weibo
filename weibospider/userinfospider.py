import re
import sys
import traceback
from collections import OrderedDict
import random
import copy
import csv
import os
import requests
from .models import UserInfo,Information
from .spider import Validator,Printer,Parser,Spider


class useriofospider(object):
    def __init__(self, config):
        self.config = config
        # change cookie from string to dict
        if type(self.config['cookie']) == type(u''):
            self.config['cookie'] = {
                t.strip().split("=")[0]: t.strip().split("=")[1]
                for t in self.config['cookie'].split(";")
            }
        self.parser = Parser(self.config)
        

    def get_nickname(self,userid):
        """获取用户昵称"""
        url = 'https://weibo.cn/%s/info' % (userid)
        selector = self.parser.deal_html(url, self.config['cookie'])
        nickname = selector.xpath('//title/text()')[0]
        nickname = nickname[:-3]
        if nickname == u'登录 - 新' or nickname == u'新浪':
            sys.exit(u'cookie错误或已过期,请重新获取')
        return nickname


    def saveuserinfo(self,userid):
        if UserInfo.objects.filter(userid=userid).exists():
            return 0
        url = 'https://weibo.cn/u/%s' % (userid)
        selector = self.parser.deal_html(url, self.config['cookie'])
        nickname = self.get_nickname(userid)  # 获取用户昵称
        user_info = selector.xpath("//div[@class='tip2']/*/text()")
        weibo_num = int(user_info[0][3:-1])
        following = int(user_info[1][3:-1])
        followers = int(user_info[2][3:-1])
        UserInfo.objects.create(nickname=nickname,userid=userid,weibo_num=weibo_num,following=following,followers=followers)


    def crawlDetailPage(self,userid,page):
        url = 'https://weibo.cn/%s/fans?page=%d' % (userid, page)
        selector = self.parser.deal_html(url, self.config['cookie'])
        fans = selector.xpath("//td/a//@href")
        userlist = []
        for item in fans:
            if re.match( r'https://weibo.cn/u/',item):
                pattern = re.compile(r'\d+')   # 查找数字
                result1 = pattern.findall(item)
                if result1[0] in userlist:
                    continue
                else:
                    self.saveuserinfo(result1[0])
                    userlist.append(result1[0])


    def get_fans(self,userid):
        idlist = []
        url = 'https://weibo.cn/%s/fans' % (userid)
        selector = self.parser.deal_html(url, self.config['cookie'])
        page_num = self.parser.get_page_num(selector)
        if page_num>5:
            num = []
            for i in range(5):
                tnum = random.randint(1, page_num)
                if tnum in num:
                    i-=1
                    continue
                idlist.append(self.crawlDetailPage(userid,tnum))
                num.append (tnum)
        else:
            for i in range(page_num):
                idlist.append(self.crawlDetailPage(userid,i))
        print(idlist)
  
def getfansinfo(userid):
    # 记得来改
    if UserInfo.objects.filter(userid = userid)[0].following == 0:
        return 0
    import json
    config_path = os.path.split(
        os.path.realpath(__file__))[0] + os.sep + 'config.json'
    if not os.path.isfile(config_path):
        sys.exit(u'当前路径：%s 不存在配置文件config.json' %
                 (os.path.split(os.path.realpath(__file__))[0] + os.sep))
    with open(config_path) as f:
        config = json.loads(f.read())
    spider = useriofospider(config)
    spider.get_fans(userid)