from django.shortcuts import render
from . import spider
from django.http import HttpResponse
from django.http import JsonResponse
from django.core import serializers
from .models import UserInfo,Information
import json 

# Create your views here.
def hello(request):
#     spider.startspider()
    return render(request, "test.html")

def getid(request):
    return render(request, "test.html")


def Inspider(request):
    try:
        user_id = request.GET.get('user_id')
        spider.startspider(user_id)
        data_info = []
        databases = Information.objects.filter(tuser= (UserInfo.objects.filter(userid=user_id)[0].id))
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
    

def showlist(request):
    return render(request, "list.html")

def test(requset):
    print('yes')
    return 