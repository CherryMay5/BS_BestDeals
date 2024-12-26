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

@csrf_exempt
def search_products(request):
    try:
        # 获取关键词和分页参数
        keyword = request.GET.get('keyword').strip()
        platforms = request.GET.get('platforms').strip()

        # 调用爬虫
        crawler(keyword)

        # 如果没有关键词，返回数据库中所有商品；有关键词时，按标题模糊查询
        if keyword:
            products = Products.objects.filter(title__icontains=keyword)

            if platforms:
                products = products.filter(platform__icontains=platforms)
        else:
            products = Products.objects.all()

        return JsonResponse({
            "success": True,
            "message": "搜索成功",
            "data": products
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False,"error": str(e) }, status=500)