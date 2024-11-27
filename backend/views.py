from django.contrib.auth import authenticate
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.

# 注册
@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            # 解析 JSON 请求数据
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            confirm_password = data.get('confirmPassword', '').strip()

            # 必填字段验证
            if not username or not email or not password or not confirm_password:
                return JsonResponse({'error': '请填写所有必填字段'}, status=400)

            # 密码长度验证
            if len(password) < 6:
                return JsonResponse({'error': '密码长度必须至少6位'}, status=400)

            # 确认密码验证
            if password != confirm_password:
                return JsonResponse({'error': '两次输入的密码不一致'}, status=400)

            # 用户名唯一性验证
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': '用户名已存在'}, status=400)

            # 邮箱唯一性验证
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': '邮箱已存在'}, status=400)

            # 创建用户
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # 返回成功响应
            return JsonResponse({'message': '注册成功'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': '请求数据格式错误，请发送 JSON 数据'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)


# 登录
@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            login_type = data.get("loginType")
            login_input = data.get("loginInput")
            password = data.get("password")

            # 根据 loginType 判断登录字段
            if login_type == "username":
                user = authenticate(username=login_input, password=password)
            elif login_type == "email":
                user_obj = User.objects.filter(email=login_input).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)
                else:
                    user = None
            else:
                return JsonResponse({"error": "无效的登录方式"}, status=400)


            if user is not None:
                login(request, user)
                return JsonResponse({'message':'登录成功'}, status=200)
            else:
                return JsonResponse({'error':'用户名或密码错误'}, status=400)

        except Exception as e:
            return JsonResponse({'error':str(e)}, status=400)
    else:
        return JsonResponse({'error':'仅支持POST请求'}, status=405)

