import datetime
import numpy as np
import csv
import os
import datetime
import codecs
from django.shortcuts import render
from . import spider
from . import judge
from django.http import HttpResponse
from .models import UserInfo,Information
from .models import Normal,Abnormal
from django.db.models import Avg,StdDev
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
import jieba
from nltk.probability import FreqDist,ConditionalFreqDist
from random import shuffle
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.naive_bayes import MultinomialNB, BernoulliNB
from django.http import HttpResponse
from django.http import JsonResponse
from django.core import serializers
from .models import UserInfo,Information
import json 
from . import userinfospider

# Create your views here.
def getid(request):
    return render(request, "test.html")
    
# def showlist(request):
#     return render(request, "list.html")

def jquery_test(req):
    return render(req, "ajax_jquery.html")

def jquery_get(req):
    print(req.GET)
    return HttpResponse("ok")


def test(tuser,num):
    tuserid = tuser
    number = num
    dec = [1]
    dec = dec*number
    ana=1
    userdata = Information.objects.filter(tuser_id = tuserid)
    l = userdata.count()
    print(l)
    le=l-number+1 
    if l<=10:
        ifdelete=0
        print("正常用户")
    else:
        i=1
        d1 = userdata.values('publish_time')[i]['publish_time']
        i=i+10
        d2 = userdata.values('publish_time')[i]['publish_time']
        d = d1 - d2 
        contentjudge=judge.predict_page(judge.build_page(userdata.values('content')[1]['content']))
        if d.days==0 and contentjudge[0]=="neg" :   
            ifdelete=1
            print("广告用户")
        else:
            ifdelete=0
            print("正常用户")
    if ifdelete==1:
        ana=1
    else:
        i=l-number
        tdata = {}
        while i<l:
            tdata = userdata[0:i]
            x=tdata.aggregate(Avg('approved_num'))['approved_num__avg']
            a=np.std(tdata.values_list('approved_num'),ddof=1)
            y=tdata.aggregate(Avg('comment_num'))['comment_num__avg']
            b=np.std(tdata.values_list('comment_num'),ddof=1)
            z=tdata.aggregate(Avg('transmit_num'))['transmit_num__avg']
            c=np.std(tdata.values_list('transmit_num'),ddof=1)
            if (abs(x - userdata.values('approved_num')[i]['approved_num'])>2*a) | (abs(userdata.values('comment_num')[i]['comment_num'])>2*b) | (abs(z - userdata.values('transmit_num')[i]['transmit_num'])>2*c):
                dec[i-l+number]=0
            i=i+1
        print("点赞转发评论",dec)
        while le < l+1 :
            i=le-number-1
            a=[]
            while i<le-2:
                d1 = userdata.values('publish_time')[i]['publish_time']
                i=i+1
                d2 = userdata.values('publish_time')[i]['publish_time']
                d = d1 - d2 
                a.append(d.days)
            a.sort()
            del a[0],a[-1]
            x=np.mean(a)
            z=np.std(a,ddof=1)
            #print (x,y,z)
            d1 = userdata.values('publish_time')[i]['publish_time']
            i=i+1
            d2 = userdata.values('publish_time')[i]['publish_time']
            d = d1 - d2
            if abs(d.days - x)>2*z:
                dec[i-l+number]=0
            #else :
                #print("error",d.days)
                #dec[i-l+number]=0
            le=le+1
        print("发博间隔",dec)
        i=l-number
        while i<l :
            tool = userdata.values('publish_tool')
            if (tool[i-1]['publish_tool'])!=(tool[i]['publish_tool']):
                    dec[i-l+number]=0
            #else :
                #print(Information.objects.all().values('publish_tool')[i-1]['publish_tool'])
                #print("wrong",i) 
                #dec[i-l+number]=0
            i=i+1
        print("工具",dec)
        i=0
        while i<number:
            if dec[i]==0:
                ana=-1
            i=i+1
        neirong=[]
        i=l-number
        while i<l:
            if dec[i-l+number]==0:
                result = userdata.values('content')[i]['content']
                neirong.append(judge.predict_page(judge.build_page(result)))
                print (neirong)
            else:
                neirong.append("x")
            i=i+1       
        i=0
        while i<number:
            if neirong[i][0]=="pos":
                dec[i]=1
            i=i+1
        print(dec)
        i=0
        while i<number:
            if dec[i]==0:
                ana=0
            i=i+1
        UserInfo.objects.filter(id=tuserid).update(status = ana) 
    return ana

    

def Inspider(request):
    try:
        user_id = request.GET.get('user_id')
        spider.startspider(user_id)
        userinfo = UserInfo.objects.filter(userid = user_id)[0]
        num = Information.objects.filter(tuser = userinfo.id).count()
        if num>4:
           statusnum = test(userinfo.id,4)
        else:
           statusnum = test(userinfo.id,1)
        
        if statusnum == 0 : status = "异常"
        elif statusnum == -1 : status = "可疑"
        else : status = "正常"
        data_info = []
        databases = Information.objects.filter(tuser = userinfo.id)
        data_info.append({
              "nickname": userinfo.nickname,
              "userid": userinfo.userid,
              "following":userinfo.following,
              "follower":userinfo.followers,
              "weibonum":userinfo.weibo_num,
              "status":status,
        })
        for item in databases:
            data = {
                "content":item.content,
                "publish_place":item.publish_place,
               
                "publish_tool":item.publish_tool,
                "approved_num":item.approved_num,
                "comment_num":item.comment_num,
                "transmit_num":item.transmit_num,
            }
            data_info.append(data)  
        return HttpResponse(json.dumps(data_info),content_type="application/json")
    except Exception as e:
        print(e)
        return ("error")
    


def userinfo(requset):
    userinfospider.getfansinfo("6153069294")


