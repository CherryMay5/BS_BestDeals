from django.urls import path
from .views import register, login,search_products
from .crawler1_tb import crawler1
from .crawler2_sn import crawler2
urlpatterns = [
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('api/crawler1_tb/', crawler1, name='crawler1_tb'),
    path('api/search_products/', search_products, name='search_products'),
    path('api/crawler2_sn/', crawler2, name='crawler2_sn'),
]


