from django.contrib import admin
from .models import Information

# Register your models here.
class InformationAdmin(admin.ModelAdmin):
    list_display = ('content','publish_time')
 
admin.site.register(Information,InformationAdmin)
