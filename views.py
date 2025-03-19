from django.shortcuts import render
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import login as auth_login
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
from .foodrecommender import FoodRecommender
import numpy as np
import pandas as pd
from collections import OrderedDict
from django.http import JsonResponse
import json
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

food_data_path = os.path.join(BASE_DIR, 'data', 'Food Order.xlsx')
model_path = os.path.join(BASE_DIR, 'models', 'knn_model.pkl')
encoder_path = os.path.join(BASE_DIR, 'models', 'encoder.pkl')
ml=FoodRecommender(food_data_path, model_path, encoder_path)
df=pd.read_excel(food_data_path)
def homepage(request):
    return render(request, 'homepage.html')
def navbar(request):
    return render(request, 'navbar.html')
def login_view(request):
    if request.user.is_authenticated:
        return redirect("homepage")
    else:
        if(request.method=="POST"):
            username=request.POST.get("username")
            password=request.POST.get("password")
            user=authenticate(request,username=username,password=password)
            if user is not None:
                login(request,user)
                messages.success(request,"You logged in successfully")
                return redirect('homepage')
            else:
                messages.error(request,"Invalid Username or Password")
                return redirect('login')
        return render(request,'login.html')

def register(request):
    data = CustomUserForm()
    if request.method == 'POST':
        data = CustomUserForm(request.POST)
        if data.is_valid():
            data.save()
            messages.success(request, "Registration successful. You can login now...")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    return render(request, 'register.html', {'form': data})
def logout_page(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect("homepage")
@login_required(login_url="login")  
def food(request):
    recommendations = []
    
    # Check if there is a food history for the user
    user_foods = FoodMl.objects.filter(username=request.user.username)
    if user_foods.exists():
        d = {}
        # Retrieve the latest searched food items for the user
        latest_foods = FoodMl.objects.filter(username=request.user.username).order_by('-time')
        
        for food in latest_foods:
            if food.food not in d:
                d[food.food] = 1
            else:
                d[food.food] += 1

        # Sort the dictionary `d` from highest to lowest value
        d = OrderedDict(sorted(d.items(), key=lambda item: item[1], reverse=True))

        # Prioritize the latest searched food
        latest_searched_food = next(iter(latest_foods)).food  # Ensure we get the actual latest searched food

        # Generate recommendations for the latest searched food
        list1 = list(ml.recommend_similar_foods(latest_searched_food, 5))
        recommendations.extend(list1)

        if len(d) == 2:
            # Get the food with the highest value in dict `d` that is not the latest searched food
            second_food = next(food for food in d if food != latest_searched_food)
            list2 = list(ml.recommend_similar_foods(second_food, 5))
            recommendations.extend(list2)
        elif len(d) >= 3:
            # Get the food with the highest and second highest value in dict `d` that are not the latest searched food
            second_food = next(food for food in d if food != latest_searched_food)
            third_food = next(food for food in d if food != latest_searched_food and food != second_food)
            list2 = list(ml.recommend_similar_foods(second_food, 5))
            list3 = list(ml.recommend_similar_foods(third_food, 5))
            recommendations.extend(list2)
            recommendations.extend(list3)
        
        # Ensure recommendations are unique
        recommendations = list(OrderedDict.fromkeys(recommendations))  # Removes duplicates and maintains order

        # Add random unique elements if necessary to reach 15 items
        if len(recommendations) < 15:
            unique_randoms = df['Name'].sample(n=15).tolist()
            random_elements = [i for i in unique_randoms if i not in recommendations]
            recommendations.extend(random_elements)

        recommended_food_names = recommendations[:15]  # Ensure exactly 15 unique recommendations

        # Query the database for food items matching the recommended food names
        recommended_foods = Food.objects.filter(name__in=recommended_food_names, availability=True)
        print(recommended_food_names)

    # If no food history exists for the user or if recommendations are empty
    if not user_foods.exists():
        recommendations=[]

        unique_randoms = df['Name'].sample(n=15).tolist()
        random_elements = [i for i in unique_randoms if i not in recommendations]
        recommendations.extend(random_elements)
        recommended_food_names = recommendations[:15]  # Ensure exactly 15 unique recommendations
        recommended_foods = Food.objects.filter(name__in=recommended_food_names, availability=True)
        print(recommended_food_names)
    return render(request, 'food.html', {'foods': recommended_foods})
@login_required(login_url="login")
def foodview(request, name):
    FoodMl.objects.create(
    username=request.user.username,
    food=name,
    )
    food= Food.objects.filter(name=name, availability=True)
    if food:
            return render(request,"foodview.html",{'food':food})
    else:
        return render(request, "foodview.html", {'error': f"No available food item found for {name}."})
def category(request, name):
    food= Food.objects.filter(availability=True, category__name=name)
    if food:
            return render(request,"category.html",{'foods':food})
    else:
        return render(request, "foodview.html", {'error': f"No available food item found for {name}."})

def search(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        query = data.get('query', '').strip()

        # Check if the query matches any food name
        food = Food.objects.filter(name__iexact=query, availability=True).first()
        if food:
            return JsonResponse({'redirect': True, 'redirect_url': f"/food/{food.name}"}, status=200)

        # Check if the query matches any category name
        category = FoodType.objects.filter(name__iexact=query).first()
        if category:
            return JsonResponse({'redirect': True, 'redirect_url': f"/category/{category.name}"}, status=200)

        # If no match is found
        return JsonResponse({'redirect': False, 'message': f"No match found for {query}. Please try again."}, status=200)
    
    return JsonResponse({'status': 'Invalid Access'}, status=400)
def cart_page(request):
  if request.user.is_authenticated:
    cart=Cart.objects.filter(user=request.user)
    return render(request,"cart.html",{"cart":cart})
  else:
    return redirect("register")



def add_cart(request):
    # Check if the request is an AJAX request and is a POST method
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            try:
                data = json.loads(request.body)
                food_qty = data.get('food_qty')
                food_id = data.get('pid')
                
                # Validate if the food item exists
                food_status = Food.objects.get(id=food_id)
                if food_status:
                    # Check if the item is already in the user's cart
                    if Cart.objects.filter(user=request.user, food_id=food_id).exists():
                        return JsonResponse({'status': 'Food already in cart'}, status=200)
                    else:
                        # Add the item to the cart
                        Cart.objects.create(user=request.user, food_id=food_id, food_qty=food_qty)
                        return JsonResponse({'status': 'Food added to cart'}, status=200)
                else:
                    return JsonResponse({'status': 'Food not found'}, status=404)
            except Food.DoesNotExist:
                return JsonResponse({'status': 'Invalid food item'}, status=400)
        else:
            return JsonResponse({'status': 'Login required'}, status=403)
    else:
        return JsonResponse({'status': 'Invalid access'}, status=400)
def remove_fav(request,fid):
  item=Favourite.objects.get(id=fid)
  item.delete()
  return redirect("favviewpage")    
def remove(request,cid):
    cartitem=Cart.objects.get(id=cid)
    cartitem.delete()
    return redirect('cart')
def favviewpage(request):
  if request.user.is_authenticated:
    fav=Favourite.objects.filter(user=request.user)
    return render(request,"fav.html",{"fav":fav})
  else:
    return redirect("register")
def fav_page(request):
    if request.headers.get('x-requested-with')=='XMLHttpRequest':
        if request.user.is_authenticated:
            data=json.load(request)
            food_id=data['pid']
            food_status=Food.objects.get(id=food_id)
            if food_status:
                if Favourite.objects.filter(user=request.user.id,food_id=food_id):
                    return JsonResponse({'status':'Food Already in Favourite'}, status=200)
                else:
                    Favourite.objects.create(user=request.user,food_id=food_id)
                    return JsonResponse({'status':'Food Added to Favourite'}, status=200)
        else:
            return JsonResponse({'status':'Login to Add Favourite'}, status=200)
    else:
        return JsonResponse({'status':'Invalid Access'}, status=200)