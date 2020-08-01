from django.contrib import admin
from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings

from . import views
 
urlpatterns = [
    url(r'show', views.manage),
    url(r'management', views.management),
] 
