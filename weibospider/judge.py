from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures
import jieba
from nltk.probability import FreqDist,ConditionalFreqDist
from random import shuffle
import csv
import os
import datetime
import numpy as np
import codecs
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.naive_bayes import MultinomialNB, BernoulliNB
from .models import UserInfo,Information
from .models import Normal,Abnormal
def text():
    i=0
    #line1=Normal.objects.all().values('ncontent')[i]['ncontent']
    l=Normal.objects.all().count()
    str=''
    while i<l:
        str+=Normal.objects.all().values('ncontent')[i]['ncontent']
        i=i+1
    #print(str)
    i=0
    l=Abnormal.objects.all().count()
    while i<l:
        str+=Abnormal.objects.all().values('acontent')[i]['acontent']
        i=i+1
    return str

    
#单个字作为特征
def bag_of_words(words):
    return dict([(word,True) for word in words])
#print(bag_of_words(text())
    
#把词语（双字）作为搭配，并通过卡方统计，选取排名前1000的词语

def bigram(words, score_fn=BigramAssocMeasures.chi_sq, n=500):
    bigram_finder = BigramCollocationFinder.from_words(words)
    bigrams = bigram_finder.nbest(score_fn, n)  # 使用卡方统计的方法，选择排名前1000的词语
    newBigrams = [u + v for (u, v) in bigrams]
    #return bag_of_words(newBigrams)
#print(bigram(text(),score_fn=BigramAssocMeasures.chi_sq,n=1000))

# 把单个字和词语一起作为特征
def bigram_words(words, score_fn=BigramAssocMeasures.chi_sq, n=500):
    bigram_finder = BigramCollocationFinder.from_words(words)
    bigrams = bigram_finder.nbest(score_fn, n)
    newBigrams = [u + v for (u, v) in bigrams]
    a = bag_of_words(words)
    b = bag_of_words(newBigrams)
    a.update(b)  # 把字典b合并到字典a中
    return a  # 所有单个字和双个字一起作为特征
#print(bigram_words(text(),score_fn=BigramAssocMeasures.chi_sq,n=1000))


stop=[line.strip() for line in open('stopwords1.txt','r',encoding='utf-8').readlines()]
i=0
l=Normal.objects.all().count()
str1=[]
while i<l:

    s1=Normal.objects.all().values('ncontent')[i]['ncontent'].split('\t')
    fenci1=jieba.cut(s1[0],cut_all=False)
    str1.append(list(set(fenci1)-set(stop)-set(['\ufeff','\n'])))
    i=i+1
i=0
str2=[]
while i<l:
    s2=Abnormal.objects.all().values('acontent')[i]['acontent'].split('\t')
    fenci2=jieba.cut(s2[0],cut_all=False)
    str2.append(list(set(fenci2)-set(stop)-set(['\ufeff','\n'])))
    i=i+1

def jieba_feature(number):
    posWords=[]
    negWords=[]
    for items in str1:
        for item in items:
            posWords.append(item)
    for items in str2:
        for item in items:
            negWords.append(item)
    word_fd=FreqDist()   # 可统计所有词的词频
    con_word_fd=ConditionalFreqDist()    # 可统计积极文本中的词频和消极文本中的词频
    for word in posWords:
        word_fd[word]+=1
        con_word_fd['pos'][word]+=1
    for word in negWords:
        word_fd[word]+=1
        con_word_fd['neg'][word]+=1
    pos_word_count=con_word_fd['pos'].N()    # 积极词的数量
    neg_word_count=con_word_fd['neg'].N()    # 消极词的数量
    # 一个词的信息量等于积极卡方统计量加上消极卡方统计量
    total_word_count=pos_word_count+neg_word_count
    word_scores={}
    best_words = []
    for word,freq in word_fd.items():
        pos_score=BigramAssocMeasures.chi_sq(con_word_fd['pos'][word],(freq,
                                                                       pos_word_count),total_word_count)
        neg_score=BigramAssocMeasures.chi_sq(con_word_fd['neg'][word],(freq,
                                                                       neg_word_count),total_word_count)
        word_scores[word]=pos_score+neg_score
        best_vals=sorted(word_scores.items(),key=lambda item: item[1],
                         reverse=True)[:number]     
        best_words=set([w for w,s in best_vals])
    return dict([(word,True) for word in best_words])


def build_features():
    #feature = bag_of_words(text())
    #feature = bigram(text(),score_fn=BigramAssocMeasures.chi_sq,n=900)
    # feature =  bigram_words(text(),score_fn=BigramAssocMeasures.chi_sq,n=900)
    feature = jieba_feature(500)  # 结巴分词
    posFeatures = []
    for items in str1:
        a = {}
        for item in items:
            if item in feature.keys():
                a[item] = 'True'
        posWords = [a, 'pos']  # 为积极文本赋予"pos"
        posFeatures.append(posWords)
    negFeatures = []
    for items in str2:
        a = {}
        for item in items:
            if item in feature.keys():
                a[item] = 'True'
        negWords = [a, 'neg']  # 为消极文本赋予"neg"
        negFeatures.append(negWords)
    return posFeatures, negFeatures

posFeatures,negFeatures=build_features()
shuffle(posFeatures)    #把文本的排列随机化
shuffle(negFeatures)
train=posFeatures[100:]+negFeatures[100:]   #只在1000条数据时合适，二八原则
test=posFeatures[:100]+negFeatures[:100]
data,tag=zip(*test)    #分离测试集合的数据和标签，便于测试

#处理输入的评论文本，使其成为可预测格式
def build_page(page):
    #四中特征提取方式
    # feature1 = bag_of_words(text())
    # n为特征维度，可调整
    # feature2 = bigram(text(),score_fn=BigramAssocMeasures.chi_sq,n=1000)
    # feature 3=  bigram_words(text(),score_fn=BigramAssocMeasures.chi_sq,n=1000)
    feature4 = jieba_feature(500)  # 结巴分词，选取1000为特征维度，可调整
    temp={}
    
    #现采用结巴分词形式处理待测文本
    fenci0=jieba.cut(page,cut_all=False)
    stop=[line.strip() for line in open('stopwords1.txt','r',encoding='utf-8').readlines()]
    for words in list(set(fenci0)-set(stop)):
        if words in feature4:
            temp[words]='True'
    return temp

#将实验比较得出的最佳分类算法（classifier_ag）构造的分类器保存
def classfier_model(classifier_ag):
    classifier = SklearnClassifier(classifier_ag)
    classifier.train(train)
    return classifier
#假设逻辑回归为最佳分类算法
classifier=classfier_model(classifier_ag=  LogisticRegression())
#用最佳分类器预测待测文本
def predict_page(page):
    pred = classifier.classify_many(page)
    return pred

def judgeuser(tuserid):
    if Information.objects.filter(tuser_id=tuserid).count()<=10:
        ifdelete=0
        print("正常用户")
    else:
        i=1
        d1 = Information.objects.filter(tuser_id=tuserid).values('publish_time')[i]['publish_time']
        i=i+10
        d2 = Information.objects.filter(tuser_id=tuserid).values('publish_time')[i]['publish_time']
        d = d1 - d2 
        contentjudge=judge.predict_page(judge.build_page(Information.objects.filter(tuser_id=tuserid).values('content')[1]['content']))
        if d.days==0 and contentjudge[0]=="neg" :   
            ifdelete=1
            print("广告用户")
        else:
            ifdelete=0
            print("正常用户")
    if ifdelete==1:
        UserInfo.objects.filter(id=tuserid).delete()
        Information.objects.filter(tuser_id=tuserid).delete()

