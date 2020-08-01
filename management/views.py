from django.shortcuts import render
from weibospider.models import UserInfo,Information,UserInfoDays
from django.http import HttpResponse
import json
# Create your views here.


def manage(request):
     userlist = UserInfo.objects.all()
     userdata = []
     for item in userlist:
          data = {
              "nickname": item.nickname,
              "userid": item.userid,
              "status":item.status,
              "days":item.days,
          }
          userdata.append(data)
     return HttpResponse(json.dumps(userdata),content_type="application/json")

def management(req):
     return render(req,'management.html')