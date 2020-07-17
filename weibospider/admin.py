from django.contrib import admin
# Register your models here.
from .models import Information
 
class InformationAdmin(admin.ModelAdmin):
    list_display = ('content','publish_time')
 
admin.site.register(Information,InformationAdmin)
