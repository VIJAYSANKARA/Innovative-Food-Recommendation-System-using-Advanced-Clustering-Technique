from django.db import models
import datetime
import os
from django.contrib.auth.models  import User
from django.utils import timezone
from datetime import datetime, timedelta
def getPictureName(request,filename):
    return os.path.join('upload_food/',filename)
class FoodType(models.Model):
    name=models.CharField(max_length=150,null=False,blank=False)
    image=models.ImageField(upload_to=getPictureName,null=False,blank=False)
    def __str__ (self):
        return self.name 
class Food(models.Model):
    name=models.CharField(max_length=150,null=False,blank=False, unique=True)
    image=models.ImageField(upload_to=getPictureName,null=False,blank=False)
    ingredients=models.CharField(max_length=150,null=False,blank=False)
    flavour_profile=models.CharField(max_length=150,null=False,blank=False)
    course=models.CharField(max_length=150,null=False,blank=False)
    state=models.CharField(max_length=150,null=False,blank=False)
    region=models.CharField(max_length=150,null=False,blank=False)
    category=models.ForeignKey(FoodType,on_delete=models.CASCADE)
    ratings=models.FloatField(null=False,blank=False)
    amount=models.IntegerField(null=False,blank=False,default=0)
    availability=models.BooleanField(default=True)
    def __str__(self):
        return self.name
    
class FoodMl(models.Model):
    username=models.CharField(max_length=150,null=False,blank=False)
    food=models.CharField(max_length=150,null=False,blank=False)
    time = models.DateTimeField(auto_now=True)
class Cart(models.Model):
  user=models.ForeignKey(User,on_delete=models.CASCADE)
  food=models.ForeignKey(Food,on_delete=models.CASCADE)
  food_qty=models.IntegerField(null=False,blank=False)
  created_at=models.DateTimeField(auto_now_add=True)
  @property
  def total_cost(self):
      return self.food_qty*self.food.amount
class Favourite(models.Model):
	user=models.ForeignKey(User,on_delete=models.CASCADE)
	food=models.ForeignKey(Food,on_delete=models.CASCADE)
	created_at=models.DateTimeField(auto_now_add=True)