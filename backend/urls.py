from django.urls import path
from .views import register, login,search_products,get_product_details,toggle_favorite,get_user_favorites
from .crawler1_tb import crawler1
from .crawler2_sn import crawler2
urlpatterns = [
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('api/crawler1_tb/', crawler1, name='crawler1_tb'),
    path('api/search_products/', search_products, name='search_products'),
    path('api/crawler2_sn/', crawler2, name='crawler2_sn'),
    path('api/get_product_details/', get_product_details, name='get_product_details'),
    path('api/toggle_favorite/', toggle_favorite, name='toggle_favorite'),
    path('api/get_user_favorites/', get_user_favorites, name='get_user_favorites'),
]


