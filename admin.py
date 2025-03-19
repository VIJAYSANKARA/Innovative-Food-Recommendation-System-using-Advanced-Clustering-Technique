from django.contrib import admin
from .models import *
class FoodAdmin(admin.ModelAdmin):
    list_display=('name',)
admin.site.register(FoodType,FoodAdmin)
admin.site.register(Food,FoodAdmin)
