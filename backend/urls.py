from django.urls import path
from .views import register, login, search_products
from .crawler import crawler
urlpatterns = [
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('api/crawler/', crawler, name='crawler'),
    path('api/search_products/', search_products, name='search_products'),
]


