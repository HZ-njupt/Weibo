from django.contrib import admin
from django.conf.urls import url,include
from django.conf.urls.static import static
from django.conf import settings

from . import views
 
urlpatterns = [
    url(r'^index/', views.getid),
    url(r'^showlist/', views.showlist),
    url(r'^spider/', views.Inspider),
    url(r'^index/', views.test),
    
] 
