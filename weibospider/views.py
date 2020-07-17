from django.shortcuts import render
from . import spider
from . import judge
from django.http import HttpResponse
from .models import UserInfo,Information
from .models import Normal,Abnormal
from django.db.models import Avg,StdDev
import datetime
import numpy as np

from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
import jieba
from nltk.probability import FreqDist,ConditionalFreqDist
from random import shuffle
import csv
import os
import datetime
import codecs
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.naive_bayes import MultinomialNB, BernoulliNB

# Create your views here.
def hello(request):
#     spider.startspider()
    return render(request, "test.html")

def getid(request):
    return render(request, "test.html")


def Inspider(request):
    try:
        userid = request.GET.get('user_id','6494237922')
        spider.startspider(userid)
        
        # print(result)
        # return render(request, "list.html", userlist)
    except Exception as e:
        print(e)
        # return (request, "list.html")
    

def showlist(request):
    #userinfo = UserInfo.objects.filter(userid = userid)
    # information = Information.objects.all()
    # userlist = {
    #     #'userinfo':userinfo,
    #     "information":information
    # }
    return render(request, "list.html")

def test(requset):
    number=19
    dec = [1]
    dec = dec*number
    #numapprove = Information.objects.all().values('approved_num')[1]['approved_num']
    #l=208
    l = Information.objects.all().count()
    print(l)
    le=l-number+1 
    i=l-number
    while i<l:
        x=Information.objects.all()[0:i-1].aggregate(Avg('approved_num'))['approved_num__avg']
        a=Information.objects.all()[0:i-1].aggregate(StdDev('approved_num'))['approved_num__stddev']
        y=Information.objects.all()[0:i-1].aggregate(Avg('comment_num'))['comment_num__avg']
        b=Information.objects.all()[0:i-1].aggregate(StdDev('comment_num'))['comment_num__stddev']
        z=Information.objects.all()[0:i-1].aggregate(Avg('transmit_num'))['transmit_num__avg']
        c=Information.objects.all()[0:i-1].aggregate(StdDev('transmit_num'))['transmit_num__stddev']
        #if (abs(x - file['点赞数'][i])>2*a) | (abs(y - file['评论数'][i])>2*b) | (abs(z - file['转发数'][i])>2*c) :
            #print("error",i,abs(x - file['点赞数'][i])>2*a,abs(y - file['评论数'][i])>2*b,abs(z - file['转发数'][i])>2*c)
        if (abs(x - Information.objects.all().values('approved_num')[i]['approved_num'])>2*a) | (abs(y - Information.objects.all().values('comment_num')[i]['comment_num'])>2*b) | (abs(z - Information.objects.all().values('transmit_num')[i]['transmit_num'])>2*c):
            dec[i-l+number]=0
        #else :
            #print("right")
        i=i+1
    print("点赞转发评论",dec)
    #numtime1 = Information.objects.all().values('publish_time')[0]['publish_time']
    #numtime2 = Information.objects.all().values('publish_time')[1]['publish_time']
    #d=numtime1-numtime2
    #print(d.days)


    while le < l+1 :
        i=le-number-1
        a=[]
        while i<le-2:
            d1 = Information.objects.all().values('publish_time')[i]['publish_time']
            i=i+1
            d2 = Information.objects.all().values('publish_time')[i]['publish_time']
            d = d1 - d2 
            a.append(d.days)
        a.sort()
        del a[0],a[-1]
        x=np.mean(a)
        z=np.std(a,ddof=1)
        #print (x,y,z)
        d1 = Information.objects.all().values('publish_time')[i]['publish_time']
        i=i+1
        d2 = Information.objects.all().values('publish_time')[i]['publish_time']
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
        if (Information.objects.all().values('publish_tool')[i-1]['publish_tool'])!=(Information.objects.all().values('publish_tool')[i]['publish_tool']):
                dec[i-l+number]=0
        #else :
            #print(Information.objects.all().values('publish_tool')[i-1]['publish_tool'])
            #print("wrong",i) 
            #dec[i-l+number]=0
        i=i+1
    print("工具",dec)
    
    
    
    #condition = []
    neirong=[]
    #for result in results['正文'][24]:
    i=l-number
    while i<l:
        if dec[i-l+number]==0:
            result = Information.objects.all().values('content')[i]['content']
            #condition.append(result)
            #condition.append(predict_page(build_page(result)))
            neirong.append(judge.predict_page(judge.build_page(result)))
            #print(condition)
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
    return HttpResponse("d")

