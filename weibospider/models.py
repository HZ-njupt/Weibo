
from django.db import models
 
# Create your models here.

class UserInfo(models.Model):
    nickname = models.CharField('用户昵称',default="无",max_length=80)
    userid = models.CharField('用户ID',default="无",max_length=80)
    weibo_num = models.PositiveIntegerField('微博数',default=0)
    following = models.PositiveIntegerField('关注数',default=0)
    followers = models.PositiveIntegerField('粉丝数',default=0)
    # isgetinfo = models.BooleanField('今日信息',default=False)
    days = models.PositiveIntegerField('检测天数',default=0)
    get_fans = models.BooleanField('获取粉丝',default=False)
    status = models.IntegerField('状态',default=1)

    def __str__(self):
        return self.userid


class Information(models.Model):
    content = models.TextField('正文',default=" ")
    publish_place = models.CharField('发布位置',default="无",max_length=64)
    publish_time = models.DateField('时间')
    publish_tool = models.CharField('发布工具',default="无",max_length=64)
    approved_num = models.PositiveIntegerField('点赞数',default=0)
    comment_num = models.PositiveIntegerField('评论数',default=0)
    transmit_num = models.PositiveIntegerField('转发数',default=0)
    tuser = models.ForeignKey("UserInfo",related_name = 'user_content')
    class Meta: 
      ordering = ('-publish_time',) 



class Abnormal(models.Model):
    acontent = models.TextField()
    def __str__(self):
        return self.acontent

class Normal(models.Model):
    ncontent = models.TextField()
    def __str__(self):
        return self.ncontent

class UserInfoDays(models.Model):
    userid = models.CharField('用户ID',default="无",max_length=80)
    nickname = models.CharField('用户昵称',default="无",max_length=80)
    following = models.PositiveIntegerField('关注数',default=0)
    time = models.DateField('日期')
    iuser = models.ForeignKey("UserInfo",related_name = 'dayuser_content')

    def __str__(self):
        return self.time