from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('warranty/', views.warranty_check, name='warranty_check'),
    path('dashboard/', views.dashboard_report, name='dashboard_report'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<str:item_key>/', views.update_cart, name='update_cart'),
    path('cart/promo/', views.apply_promo, name='apply_promo'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
