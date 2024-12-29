from sqlite3 import IntegrityError
from sys import platform

from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
import json

from openpyxl.compat.product import product

from backend.models import Products, ProductFavorite, PriceHistory
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


@csrf_exempt
def search_products(request):
        try:
            search_input = request.GET.get('keyword', '')
            select_platform = request.GET.get('select_platform', '')
            price_order = request.GET.get('price_order', '')
            category_select = request.GET.get('category_select', '')

            # 初始化查询集
            products = Products.objects.all()

            # 根据搜索内容查询：有关键词时，按标题模糊查询
            if search_input:
                products = products.filter(title__icontains=search_input)

            # 根据平台过滤
            if select_platform:
                products = products.filter(platform_belong=select_platform)

            # 根据品类筛选
            if category_select:
                products = products.filter(category__icontains=category_select)

            # 根据价格排序
            if price_order == "asc" :
                products = products.order_by("price") # 按价格升序
            elif price_order == "desc" :
                products = products.order_by("-price") # 按价格降序

            if not products:
                # 调用爬虫，重新search
                if select_platform == "淘宝":
                    crawler1(search_input)
                elif select_platform == "苏宁易购" :
                    crawler1(search_input)
                else:
                    crawler1(search_input)
                    crawler1(search_input)
                # 爬虫获取完数据后重新搜索
                search_products(search_input)

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
            'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': product.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'platform_belong': product.platform_belong,
            'category':product.category,
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
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': product.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'platform_belong': product.platform_belong,
                'category':product.category,
            })

        print(product_data)
        # 转换为 JSON 格式返回
        # data = list(favorites.values())
        return JsonResponse(product_data, safe=False)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
def get_user_info(request):
    try :
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({"error": "用户ID未提供"}, status=400)

        # 确保用户存在
        user = get_object_or_404(User, id=user_id)

        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }

        return JsonResponse(user_info, status=200)
    except Exception as e:
        return JsonResponse({'error': '无法获取个人信息', 'details': str(e)}, status=500)

import random

def generate_verification_code():
    return f"{random.randint(100000, 999999)}"

@csrf_exempt
def send_password_verification_code(request):
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({'error': '未获取到用户ID'}, status=400)

        des_email = User.objects.get(id=user_id).email
        code = generate_verification_code()
        content = f"您的验证码是： {code} "
        res = send_mail('Best Deals 商品比价网站 —— 用户操作：修改密码',
                        content,
                        settings.DEFAULT_FROM_EMAIL,
                        [des_email])
        data = {
            'verify_code': code
        }
        if res == 1:
            return JsonResponse(data, status=200)
        else:
            return JsonResponse({'error': '邮件发送失败'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def update_username(request):
    try:
        user_id = request.GET.get('user_id')
        new_username = request.GET.get('new_username')

        if not user_id:
            return JsonResponse({"error": "用户ID未提供"}, status=400)
        if not new_username:
            return JsonResponse({'error': '用户名不能为空'}, status=400)
        if User.objects.filter(username=new_username).exists():
            return JsonResponse({'error': '用户名已存在,请重新输入'}, status=400)

        # 确保用户存在
        user = get_object_or_404(User, id=user_id)
        # 更新用户名
        user.username = new_username
        user.save()

        return JsonResponse({"message": "用户名更新成功", "new_username": new_username}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def update_password(request):
    try:
        user_id = request.GET.get('user_id')
        new_password = request.GET.get('new_password')

        if not user_id:
            return JsonResponse({"error": "用户ID未提供"}, status=400)
        if not new_password:
            return JsonResponse({'error': '不能为空'}, status=400)

        # 检查密码长度
        if len(new_password) < 6:
            return JsonResponse({'error': '密码长度不能少于六位'}, status=400)

        # 确保用户存在
        user = get_object_or_404(User, id=user_id)
        # 更新用户密码
        user.set_password(new_password)
        user.save()  # 放到数据库里

        return JsonResponse({"message": "密码更新成功", "new_password": new_password}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from django.core.mail import send_mail
@csrf_exempt
def send_verify_email(request):
    try:
        des_email = request.GET.get('des_email')
        if not des_email:
            return JsonResponse({'error': '邮箱地址不能为空'}, status=400)

        code = generate_verification_code()
        content = f"您的验证码是： {code}   修改后的邮箱为：{des_email}"
        res = send_mail('Best Deals 商品比价网站 —— 用户操作：修改邮箱',
                         content,
                         settings.DEFAULT_FROM_EMAIL,
                         [des_email])
        data = {
            'verify_code':code
        }
        if res == 1:
            return JsonResponse(data, status=200)
        else:
            return JsonResponse({'error':'邮件发送失败'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def update_email(request):
    try:
        user_id = request.GET.get('user_id')
        new_email = request.GET.get('new_email')

        if not user_id:
            return JsonResponse({"error": "用户ID未提供"}, status=400)
        if not new_email:
            return JsonResponse({'error': '邮箱地址不能为空'}, status=400)

        # 确保用户存在
        user = get_object_or_404(User, id=user_id)
        # 更新用户邮箱
        user.email = new_email
        user.save()

        return JsonResponse({"message": "邮箱更新成功", "new_email": new_email}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def get_price_history(request):
    try:
        product_id = request.GET.get('product_id')
        if not product_id:
            return JsonResponse({'error':'未能成功传入product_id'}, status=400)

        price_histories = PriceHistory.objects.filter(product_id=product_id).order_by('recorded_at')

        data = [
            {
                'price':ph.price,
                'recorded_at':ph.recorded_at.strftime('%Y.%m.%d')
            }
            for ph in price_histories
        ]

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def send_price_email(user_id,product_id):
    try:
        product = get_object_or_404(Products, id=product_id)
        product_title = product.title

        user = get_object_or_404(User, id=user_id)
        des_email = user.email

        content = f'你关注的商品“{product_title}”降价啦！快来看看吧~'
        res = send_mail('降价提醒！',
                         content,
                         settings.DEFAULT_FROM_EMAIL,
                         [des_email])
        data = {
            'send_content':content
        }
        if res == 1:
            return 1
        else:
            return 0
    except Exception as e:
        print("error：",str(e))
        return 0