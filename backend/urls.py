from django.urls import path
from .views import register, login
from .views import search_products,get_product_details
from .views import toggle_favorite,get_user_favorites
from .views import get_user_info,send_verify_email,update_email
from .views import get_price_history
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
    path('api/get_user_info/', get_user_info, name='get_user_info'),
    path('api/send_verify_email/', send_verify_email, name='send_verify_email'),
    path('api/update_email/', update_email, name='update_email'),
    path('api/get_price_history/', get_price_history, name='get_price_history'),
]


