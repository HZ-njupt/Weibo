# -*- coding: UTF-8 -*-
import re
import sys
import traceback
from collections import OrderedDict
from datetime import date, datetime, timedelta

import random
import copy
import csv
import os
from lxml import etree
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from time import sleep
from .models import UserInfo,Information
from django.conf import settings


user_id_list = []
stable_user_id = []
danger_user_id = []
class Parser:
    def __init__(self, config):
        self.config = config

    def deal_html(self, url, cookie):
        """处理html"""
        print("url:", url)
        html = requests.get(url, cookies=cookie).content
        selector = etree.HTML(html)
        return selector

    def deal_garbled(self, info):
        """处理乱码"""
        info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
            sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
        return info

    def extract_picture_urls(self, info, weibo_id):
        """提取微博原始图片url"""
        try:
            a_list = info.xpath('div/a/@href')
            first_pic = 'https://weibo.cn/mblog/pic/' + weibo_id + '?rl=0'
            all_pic = 'https://weibo.cn/mblog/picAll/' + weibo_id + '?rl=1'
            if first_pic in a_list:
                if all_pic in a_list:
                    selector = self.deal_html(all_pic, self.config['cookie'])
                    preview_picture_list = selector.xpath('//img/@src')
                    picture_list = [
                        p.replace('/thumb180/', '/large/')
                        for p in preview_picture_list
                    ]
                    picture_urls = ','.join(picture_list)
                else:
                    if info.xpath('.//img/@src'):
                        preview_picture = info.xpath('.//img/@src')[-1]
                        picture_urls = preview_picture.replace(
                            '/wap180/', '/large/')
                    else:
                        sys.exit(
                            u"爬虫微博可能被设置成了'不显示图片'，请前往"
                            u"'https://weibo.cn/account/customize/pic'，修改为'显示'"
                        )
            else:
                picture_urls = u'无'
            return picture_urls
        except Exception:
            return u'无'

    def get_picture_urls(self, info, is_original):
        """获取微博原始图片url"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            picture_urls = {}
            if is_original:
                original_pictures = self.extract_picture_urls(info, weibo_id)
                picture_urls['original_pictures'] = original_pictures
                if not self.config['filter']:
                    picture_urls['retweet_pictures'] = u'无'
            else:
                retweet_url = info.xpath("div/a[@class='cc']/@href")[0]
                retweet_id = retweet_url.split('/')[-1].split('?')[0]
                retweet_pictures = self.extract_picture_urls(info, retweet_id)
                picture_urls['retweet_pictures'] = retweet_pictures
                a_list = info.xpath('div[last()]/a/@href')
                original_picture = u'无'
                for a in a_list:
                    if a.endswith(('.gif', '.jpeg', '.jpg', '.png')):
                        original_picture = a
                        break
                picture_urls['original_pictures'] = original_picture
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_video_url(self, info, is_original):
        """获取微博视频url"""
        try:
            if is_original:
                div_first = info.xpath('div')[0]
                a_list = div_first.xpath('.//a')
                video_link = u'无'
                for a in a_list:
                    if 'm.weibo.cn/s/video/show?object_id=' in a.xpath(
                            '@href')[0]:
                        video_link = a.xpath('@href')[0]
                        break
                if video_link != u'无':
                    video_link = video_link.replace(
                        'm.weibo.cn/s/video/show', 'm.weibo.cn/s/video/object')
                    wb_info = requests.get(
                        video_link, cookies=self.config['cookie']).json()
                    video_url = wb_info['data']['object']['stream'].get(
                        'hd_url')
                    if not video_url:
                        video_url = wb_info['data']['object']['stream']['url']
                        if not video_url:  # 说明该视频为直播
                            video_url = u'无'
            else:
                video_url = u'无'
            return video_url
        except Exception:
            return u'无'

    def get_page_num(self, selector):
        """获取微博总页数"""

        if selector.xpath("//input[@name='mp']") == []:
            page_num = 1
        else:
            page_num = (int)(
                selector.xpath("//input[@name='mp']")[0].attrib['value'])
        return page_num

    def get_long_weibo(self, weibo_link):
        """获取长原创微博"""

        selector = self.deal_html(weibo_link, self.config['cookie'])
        info = selector.xpath("//div[@class='c']")[1]
        wb_content = self.deal_garbled(info)
        wb_time = info.xpath("//span[@class='ct']/text()")[0]
        weibo_content = wb_content[wb_content.find(':') +
                                   1:wb_content.rfind(wb_time)]
        return weibo_content

    def get_original_weibo(self, info, weibo_id):
        """获取原创微博"""

        weibo_content = self.deal_garbled(info)
        weibo_content = weibo_content[:weibo_content.rfind(u'赞')]
        a_text = info.xpath('div//a/text()')
        if u'全文' in a_text:
            weibo_link = 'https://weibo.cn/comment/' + weibo_id
            wb_content = self.get_long_weibo(weibo_link)
            if wb_content:
                weibo_content = wb_content
        return weibo_content

    def get_long_retweet(self, weibo_link):
        """获取长转发微博"""
        wb_content = self.get_long_weibo(weibo_link)
        weibo_content = wb_content[:wb_content.rfind(u'原文转发')]
        return weibo_content

    def get_retweet(self, info, weibo_id):
        """获取转发微博"""
        wb_content = self.deal_garbled(info)
        wb_content = wb_content[wb_content.find(':') +
                                1:wb_content.rfind(u'赞')]
        wb_content = wb_content[:wb_content.rfind(u'赞')]
        a_text = info.xpath('div//a/text()')
        if u'全文' in a_text:
            weibo_link = 'https://weibo.cn/comment/' + weibo_id
            weibo_content = self.get_long_retweet(weibo_link)
            if weibo_content:
                wb_content = weibo_content
        retweet_reason = self.deal_garbled(info.xpath('div')[-1])
        retweet_reason = retweet_reason[:retweet_reason.rindex(u'赞')]
        original_user = info.xpath("div/span[@class='cmt']/a/text()")
        if original_user:
            original_user = original_user[0]
            wb_content = (retweet_reason + '\n' + u'原始用户: ' + original_user +
                          '\n' + u'转发内容: ' + wb_content)
        else:
            wb_content = retweet_reason + '\n' + u'转发内容: ' + wb_content
        return wb_content

    def is_original(self, info):
        """判断微博是否为原创微博"""
        is_original = info.xpath("div/span[@class='cmt']")
        if len(is_original) > 3:
            return False
        else:
            return True

    def get_weibo_content(self, info, is_original):
        """获取微博内容"""
        weibo_id = info.xpath('@id')[0][2:]
        if is_original:
            weibo_content = self.get_original_weibo(info, weibo_id)
        else:
            weibo_content = self.get_retweet(info, weibo_id)
        return weibo_content

    def get_publish_place(self, info):
        """获取微博发布位置"""
        div_first = info.xpath('div')[0]
        a_list = div_first.xpath('a')
        publish_place = u'无'
        for a in a_list:
            if ('place.weibo.com' in a.xpath('@href')[0]
                    and a.xpath('text()')[0] == u'显示地图'):
                weibo_a = div_first.xpath("span[@class='ctt']/a")
                if len(weibo_a) >= 1:
                    publish_place = weibo_a[-1]
                    if (u'视频' == div_first.xpath("span[@class='ctt']/a/text()")
                        [-1][-2:]):
                        if len(weibo_a) >= 2:
                            publish_place = weibo_a[-2]
                        else:
                            publish_place = u'无'
                    publish_place = self.deal_garbled(publish_place)
                    break
        return publish_place

    def get_publish_time(self, info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            publish_time = str_time.split(u'来自')[0]
            if u'刚刚' in publish_time:
                publish_time = datetime.now().strftime('%Y-%m-%d')
            elif u'分钟' in publish_time:
                # minute = publish_time[:publish_time.find(u'分钟')]
                # minute = timedelta(minutes=int(minute))
                # publish_time = (datetime.now() -
                #                 minute).strftime('%Y-%m-%d %H:%M')
                publish_time = datetime.now().strftime('%Y-%m-%d')
            elif u'今天' in publish_time:
                today = datetime.now().strftime('%Y-%m-%d')
                # time = publish_time[3:]
                publish_time = today
                if len(publish_time) > 10:
                    publish_time = publish_time[:10]
            elif u'月' in publish_time:
                year = datetime.now().strftime('%Y')
                month = publish_time[0:2]
                day = publish_time[3:5]
                # time = publish_time[7:12]
                publish_time = year + '-' + month + '-' + day
            else:
                publish_time = publish_time[:10]
            return publish_time
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_tool(self, info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            if len(str_time.split(u'来自')) > 1:
                publish_tool = str_time.split(u'来自')[1]
            else:
                publish_tool = u'无'
            return publish_tool
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_weibo_footer(self, info):
        """获取微博点赞数、转发数、评论数"""
        try:
            footer = {}
            pattern = r'\d+'
            str_footer = info.xpath('div')[-1]
            str_footer = self.deal_garbled(str_footer)
            str_footer = str_footer[str_footer.rfind(u'赞'):]
            weibo_footer = re.findall(pattern, str_footer, re.M)

            up_num = int(weibo_footer[0])
            footer['up_num'] = up_num

            retweet_num = int(weibo_footer[1])
            footer['retweet_num'] = retweet_num

            comment_num = int(weibo_footer[2])
            footer['comment_num'] = comment_num
            return footer
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_one_weibo(self, info,id):
        """获取一条微博的全部信息"""
        try:
            weibo = OrderedDict()
            is_original = self.is_original(info)
            if (not self.config['filter']) or is_original:
                weibo['id'] = info.xpath('@id')[0][2:]
                weibo['content'] = self.get_weibo_content(info,
                                                          is_original)  # 微博内容
                weibo['publish_place'] = self.get_publish_place(info)  # 微博发布位置
                weibo['publish_time'] = self.get_publish_time(info)  # 微博发布时间
                weibo['publish_tool'] = self.get_publish_tool(info)  # 微博发布工具
                footer = self.get_weibo_footer(info)
                weibo['up_num'] = footer['up_num']  # 微博点赞数
                weibo['retweet_num'] = footer['retweet_num']  # 转发数
                weibo['comment_num'] = footer['comment_num']  # 评论数

                picture_urls = self.get_picture_urls(info, is_original)
                weibo['original_pictures'] = picture_urls[
                    'original_pictures']  # 原创图片url
                if not self.config['filter']:
                    weibo['retweet_pictures'] = picture_urls[
                        'retweet_pictures']  # 转发图片url
                    weibo['original'] = is_original  # 是否原创微博
                weibo['video_url'] = self.get_video_url(info,
                                                        is_original)  # 微博视频url
            else:
                weibo = None
            #qs = UserInfo.objects.filter(userid=id)[2]
            #print(qs)
            qs = UserInfo.objects.filter(userid=id)[0]
            Information.objects.create(content=weibo['content'],publish_place=weibo['publish_place'],publish_time=weibo['publish_time'],publish_tool=weibo['publish_tool'],approved_num=weibo['up_num'],comment_num=weibo['comment_num'],transmit_num=weibo['retweet_num'],tuser=qs)
            return weibo
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def is_pinned_weibo(self, info):
        """判断微博是否为置顶微博"""
        kt = info.xpath(".//span[@class='kt']/text()")
        if kt and kt[0] == u'置顶':
            return True
        else:
            return False


class Printer:
    def print_one_weibo(self, weibo):
        """打印一条微博"""
        print(weibo['content'])
        print(u'微博发布位置：%s' % weibo['publish_place'])
        print(u'微博发布时间：%s' % weibo['publish_time'])
        print(u'微博发布工具：%s' % weibo['publish_tool'])
        print(u'点赞数：%d' % weibo['up_num'])
        print(u'转发数：%d' % weibo['retweet_num'])
        print(u'评论数：%d' % weibo['comment_num'])

    def print_user_info(self, user):
        """打印微博用户信息"""
        print(u'用户昵称: %s' % user['nickname'])
        print(u'用户id: %s' % user['id'])
        print(u'微博数: %d' % user['weibo_num'])
        print(u'关注数: %d' % user['following'])
        print(u'粉丝数: %d' % user['followers'])



def is_date(since_date):
    """判断日期格式是否正确"""
    try:
        datetime.strptime(since_date, "%Y-%m-%d")
        return True
    except:
        return False


class Validator:
    def __init__(self, config):
        """
        self.user_id_list = ''  # 1. 用户id list,如昵称为"Dear-迪丽热巴"的id为'1669879400'；2. 存储用户id list 的文件名
        self.since_date = since_date  # 1. 起始时间，即爬取发布日期从该值到现在的微博，形式为yyyy-mm-dd 2. 起始时间距离今天的天数，形式为一个整数
        self.filter = filter  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        self.mongodb_write = mongodb_write  # 值为0代表不将结果写入MongoDB数据库,1代表写入
        self.mysql_write = mysql_write  # 值为0代表不将结果写入MySQL数据库,1代表写入
        self.pic_download = pic_download  # 取值范围为0、1,程序默认值为0,代表不下载微博原始图片,1代表下载
        self.video_download = video_download  # 取值范围为0、1,程序默认为0,代表不下载微博视频,1代表下载
        self.mysql_config = {
        }  # MySQL数据库连接配置，可以不填，当使用者的mysql用户名、密码等与本程序默认值不同时，需要通过mysql_config来自定义
        """
        self.config = config

    def validate(self):
        bool_config = ["filter", "pic_download", "video_download"]
        date_config = ["since_date"]

        for key in bool_config:
            if self.config[key] not in [0, 1]:
                sys.exit("%s值应为0或1,请重新输入" % key)
        for key in date_config:
            if not (type(self.config[key]) == type(0)
                    or is_date(self.config[key])):
                sys.exit("%s值应为yyyy-mm-dd形式或整数,请重新输入" % key)
        for mode in self.config['write_mode']:
            if mode not in ['txt', 'csv', 'mysql', 'mongo']:
                sys.exit("write_mode值应为txt,csv,mysql,mongo,请重新输入")


def get_filepath(type, nickname):
    """获取结果文件路径"""
    file_dir = os.path.split(
        os.path.realpath(__file__))[0] + os.sep + 'weibo' + os.sep + nickname
    if type == 'img' or type == 'video':
        file_dir = file_dir + os.sep + type
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    if type == 'img' or type == 'video':
        return file_dir
    file_path = file_dir + os.sep + nickname + '.' + type
    return file_path


def write_log(since_date):
    """当程序因cookie过期停止运行时，将相关信息写入log.txt"""
    file_dir = os.path.split(
        os.path.realpath(__file__))[0] + os.sep + 'weibo' + os.sep
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    file_path = file_dir + 'log.txt'
    content = u'cookie已过期，从%s到今天的微博获取失败，请重新设置cookie\n' % since_date
    with open(file_path, 'ab') as f:
        f.write(content.encode(sys.stdout.encoding))



class Spider(object):
    def __init__(self, config,userid,sincedate):
        """Weibo类初始化"""
        self.config = config
        # change cookie from string to dict
        if type(self.config['cookie']) == type(u''):
            self.config['cookie'] = {
                t.strip().split("=")[0]: t.strip().split("=")[1]
                for t in self.config['cookie'].split(";")
            }
        self.config['user_id_list'].append(userid)
        self.config["since_date"] = sincedate-1
        if type(self.config['since_date']) == type(0):
            self.config['since_date'] = str(
                date.today() - timedelta(self.config['since_date']))

        self.validator = Validator(self.config)
        self.validator.validate()
        self.printer = Printer()
        #self.writer = MysqlWriter(self.config)
        #self.downloader = Downloader(self.config)
        self.parser = Parser(self.config)

    def get_nickname(self):
        """获取用户昵称"""
        url = 'https://weibo.cn/%s/info' % (self.user['id'])
        selector = self.parser.deal_html(url, self.config['cookie'])
        nickname = selector.xpath('//title/text()')[0]
        nickname = nickname[:-3]
        if nickname == u'登录 - 新' or nickname == u'新浪':
            write_log(self.config['since_date'])
            sys.exit(u'cookie错误或已过期,请重新获取')
        
        self.user['nickname'] = nickname
        #UserInfo.nickname = nickname

    def get_user_info(self, selector):
        """获取用户昵称、微博数、关注数、粉丝数"""
        self.get_nickname()  # 获取用户昵称
        user_info = selector.xpath("//div[@class='tip2']/*/text()")

        self.user['weibo_num'] = int(user_info[0][3:-1])
        self.user['following'] = int(user_info[1][3:-1])
        self.user['followers'] = int(user_info[2][3:-1])
        # UserInfo.weibo_num = int(user_info[0][3:-1])
        # UserInfo.following = int(user_info[1][3:-1])
        # UserInfo.followers = int(user_info[2][3:-1])
        UserInfo.objects.create(nickname=self.user['nickname'],userid=self.user['id'],weibo_num=self.user['weibo_num'],following=self.user['following'],followers=self.user['followers'])
        self.printer.print_user_info(self.user)
        #self.writer.write_user(self.user)
        print('*' * 100)

    def get_one_page(self, page):
        """获取第page页的全部微博"""
        url = 'https://weibo.cn/u/%s?page=%d' % (self.user['id'], page)
        selector = self.parser.deal_html(url, self.config['cookie'])
        info = selector.xpath("//div[@class='c']")
        is_exist = info[0].xpath("div/span[@class='ctt']")
        if is_exist:
            for i in range(0, len(info) - 2):
                if i==0:
                    continue
                weibo = self.parser.get_one_weibo(info[i],self.user['id'])
                if weibo:
                    if weibo['id'] in self.weibo_id_list:
                        continue
                    publish_time = datetime.strptime(
                        weibo['publish_time'][:10], "%Y-%m-%d")
                    since_date = datetime.strptime(self.config['since_date'],
                                                   "%Y-%m-%d")
                    if publish_time < since_date:
                        if self.parser.is_pinned_weibo(info[i]):
                            continue
                        else:
                            return True
                    self.printer.print_one_weibo(weibo)

                    self.weibo.append(weibo)
                    self.weibo_id_list.append(weibo['id'])
                    self.got_num += 1
                    print('-' * 100)

                    #self.writer.write_weibo([weibo])

    def get_weibo_info(self):
        """获取微博信息"""
        url = 'https://weibo.cn/u/%s' % (self.user['id'])
        selector = self.parser.deal_html(url, self.config['cookie'])
        if UserInfo.objects.filter(userid = self.user['id']).exists():
            print("用户存在")
        else:
            self.get_user_info(selector)  # 获取用户昵称、微博数、关注数、粉丝数

        page_num = self.parser.get_page_num(selector)  # 获取微博总页数
        page1 = 0
        random_pages = random.randint(1, 5)
        for page in tqdm(range(1, page_num + 1), desc='Progress'):
            is_end = self.get_one_page(page)  # 获取第page页的全部微博
            if is_end:
                break

            # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
            # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
            # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
            if page - page1 == random_pages and page < page_num:
                sleep(random.randint(6, 10))
                page1 = page
                random_pages = random.randint(1, 5)

        if not self.config['filter']:
            print(u'共爬取' + str(self.got_num) + u'条微博')
        else:
            print(u'共爬取' + str(self.got_num) + u'条原创微博')

    def initialize_info(self, userid):
        """初始化爬虫信息"""
        self.got_num = 0  # 爬取到的微博数
        self.weibo = []  # 存储爬取到的所有微博信息
        self.user = {'id': userid}  # 存储爬取到的用户信息
        self.weibo_id_list = []  # 存储爬取到的所有微博id

    def start(self):
        """运行爬虫"""
        for userid in self.config['user_id_list']:
            self.initialize_info(userid)
            print('*' * 100)
            self.get_weibo_info()
            print(u'信息抓取完毕')
            print('*' * 100)
            




def startspider(userid):
    sinceday = 1
    if UserInfo.objects.filter(userid=userid).exists():
        tdata = Information.objects.filter(tuser_id = UserInfo.objects.filter(userid=userid)[0].id)
        Idate = date.today() - tdata[0].publish_time
        if Idate.days == 0:
            return 0
        sinceday = Idate.days
    import json
    config_path = os.path.split(
        os.path.realpath(__file__))[0] + os.sep + 'config.json'
    if not os.path.isfile(config_path):
        sys.exit(u'当前路径：%s 不存在配置文件config.json' %
            (os.path.split(os.path.realpath(__file__))[0] + os.sep))
    with open(config_path) as f:
        config = json.loads(f.read())
    spider = Spider(config,userid,sinceday)
    spider.start()  # 爬取微博信息


