from django.urls import path
from django.urls import include
from .views import product_list_api, banners_list_api, register_order


app_name = "foodcartapp"

urlpatterns = [
    path('products/', product_list_api),
    path('banners/', banners_list_api),
    path('order/', register_order),
    path('api-auth/', include('rest_framework.urls')),
]
