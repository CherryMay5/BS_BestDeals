from sqlite3 import IntegrityError
from sys import platform

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
import json

from backend.models import Products, ProductFavorite
from .crawler1_tb import crawler1
from .crawler2_sn import crawler2


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
            return JsonResponse({'message': '登录成功', 'username': user.username, 'email': user.email, 'user_id': user.id}, status=200)
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
# class ProductSearchPagination(PageNumberPagination):
#     page_size = 40  # 每页40个商品
#     page_size_query_param = 'page_size'
#     max_page_size = 100 # 最大页数设置

@csrf_exempt
def search_products(request):
        try:
            search_input = request.GET.get('keyword', '')
            platforms = request.GET.getlist('platforms', [])

            # 初始化查询集
            products = Products.objects.all()

            if search_input:
                products = products.filter(title__icontains=search_input)
                # 根据平台过滤
                if platforms:
                    products = products.filter(platform_belong__in=platforms)
            else:
                # 如果没有关键词，返回数据库中所有商品；有关键词时，按标题模糊查询
                # 调用爬虫
                crawler1(search_input)
                crawler2(search_input)

            print(products)

            # 转换为 JSON 格式返回
            data = list(products.values())
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({"success": False,"error": str(e) }, status=500)


from django.shortcuts import get_object_or_404
@csrf_exempt
def get_product_details(request):
    try:
        # 从请求中获取商品的 ID
        product_id = request.GET.get('product_id')
        user_id = request.GET.get('user_id')
        print("登录用户 user_id = ",user_id)
        print("正在查找商品详情 product_id = ",product_id)

        if not product_id:
            return JsonResponse({'error': '缺少商品ID参数'}, status=400)
        # 查询商品
        product = get_object_or_404(Products, id=product_id)

        is_favorite = False
        if user_id:
            user = get_object_or_404(User, id=user_id)
            is_favorite = ProductFavorite.objects.filter(user=user, product_id=product_id).exists()

        # 将商品信息转换为字典格式
        product_data = {
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
            'created_at': product.created_at,
            'updated_at': product.updated_at,
            'platform_belong': product.platform_belong,
            'is_favorite': is_favorite,
        }

        return JsonResponse(product_data, status=200)

    except Exception as e:
        return JsonResponse({'error': '无法获取商品详情', 'details': str(e)}, status=500)


@csrf_exempt
def toggle_favorite(request):
    try:
        # 获取用户和商品信息
        user_id = request.GET.get('user_id')
        product_id = request.GET.get('product_id')

        if not user_id or not product_id:
            return JsonResponse({'error': '缺少 user_id 或 product_id 参数'}, status=400)

        user_choose = get_object_or_404(User, id=user_id)
        product_choose = get_object_or_404(Products, id=product_id)

        # 检查是否已收藏
        favorite, created = ProductFavorite.objects.get_or_create(
            user=user_choose,
            product=product_choose
        )

        if created:
            # 如果已收藏，则取消收藏

            is_favorite = True
        else:
            favorite.delete()
            is_favorite = False  # 假设1表示已收藏，0表示未收藏
        print("现在收藏状态：",is_favorite)
        return JsonResponse({'is_favorite': is_favorite})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_user_favorites(request):
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({"error": "用户ID未提供"}, status=400)

        # 确保用户存在
        user = get_object_or_404(User, id=user_id)

        # 初始化查询集:获取当前用户收藏的商品
        favorites = ProductFavorite.objects.filter(user=user).select_related('product')
        print(favorites)

        # 构造返回的数据
        product_data = []
        for favorite in favorites:
            product = favorite.product
            # 将商品信息转换为字典格式
            product_data.append({
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
                'created_at': product.created_at,
                'updated_at': product.updated_at,
                'platform_belong': product.platform_belong,
            })

        print(product_data)
        # 转换为 JSON 格式返回
        # data = list(favorites.values())
        return JsonResponse(product_data, safe=False)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

