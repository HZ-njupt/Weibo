import os
import django
from bs4 import BeautifulSoup
import requests
 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Weibo.settings")#website可以更改为自己的项目名称
# django.setup()#Django版本大于1.7 加入这行代码
 
def spider_Information():
    global new
    from weibospider.models import Information
    first = BeautifulSoup(str(new[0]),'html.parser')
    first_new = first.find_all('tr')
    for i in range(20):
        first_new_td = BeautifulSoup(str(first_new[i+1]),'html.parser')
        first_new_item = first_new_td.find_all('td')
        Information.objects.create(title=first_new_item[1].text,number=first_new_item[0].text,clicks=first_new_item[2].text,time=first_new_item[3].text)
 
if __name__ == "__main__":
    url = 'http://news.ifeng.com/hotnews/'
    req = requests.get(url)
    html = req.content.decode('utf-8')
    div_bf = BeautifulSoup(html,'html.parser')
    new = div_bf.find_all('div',class_='boxTab clearfix')
    spider_Information()
    print('Information Done!')
