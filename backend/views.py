from sqlite3 import IntegrityError
from sys import platform

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
import json

from backend.models import Products
from backend.crawler import crawler

@csrf_exempt
def register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': '用户名已存在'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': '邮箱已存在'}, status=400)

        print(request.body)  # 打印原始请求体

        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            new_user.save() # 放到数据库里
            return JsonResponse({'message': '注册成功'}, status=201)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误，请发送 JSON 数据'}, status=400)
    except Exception as e1:
        return JsonResponse({'error': '服务器内部错误'}, status=500)


@csrf_exempt
def login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        print(request.body)  # 打印原始请求体

        user = authenticate(username=username, password=password)
        if user is not None:
            return JsonResponse({'message': '登录成功', 'username': user.username, 'email': user.email}, status=200)
        else:
            return JsonResponse({'error': '用户名或密码错误'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误，请发送 JSON 数据'}, status=400)
    except Exception as e:
        return JsonResponse({'error': '服务器内部错误'}, status=500)


from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Products
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

# 商品分页类
class ProductSearchPagination(PageNumberPagination):
    page_size = 40  # 每页40个商品
    page_size_query_param = 'page_size'
    max_page_size = 100 # 最大页数设置

# 商品展示接口
class ProductSearchView(APIView):
    def post(self, request):
# @csrf_exempt
# def search_products(request):
        try:
            search_input = request.data.get('keyword', '')
            platforms = request.data.get('platforms', [])

            # 调用爬虫
            # crawler(search_input)

            # 如果没有关键词，返回数据库中所有商品；有关键词时，按标题模糊查询
            if search_input:
                products = Products.objects.filter(title__icontains=search_input)
                # 根据平台过滤
                if platforms:
                    products = products.filter(platform__icontains=platforms)
            else:
                products = Products.objects.all()
                # 调用爬虫
                # crawler(search_input)

            paginator = ProductSearchPagination()
            result_page = paginator.paginate_queryset(products, request)

            product_data = [{
                'id': product.id,
                'title': product.title,
                'price': product.price,
                'deal': product.deal,
                'location': product.location,
                'shop': product.shop,
                'is_post_free': product.is_post_free,
                'title_url': product.title_url,
                'shop_url': product.shop_url,
                'img_url': product.img_url,
                'style': product.style,
                'platform_belong': product.platform_belong,
            } for product in result_page]

            print(product_data)
            return paginator.get_paginated_response(product_data)
            # return JsonResponse({
            #     "success": True,
            #     "message": "搜索成功",
            #     "data": products
            # }, status=200)
        except Exception as e:
            return JsonResponse({"success": False,"error": str(e) }, status=500)