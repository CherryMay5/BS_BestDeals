from django.urls import path
from .views import register, login
from .crawler import crawler
urlpatterns = [
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('api/crawler/', crawler, name='crawler'),
]


