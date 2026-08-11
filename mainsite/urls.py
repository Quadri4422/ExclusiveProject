from django.urls import path
from . import views

app_name = 'mainsite'

urlpatterns = [
    path('', views.index, name='index'),    
    path('categories/', views.categories, name='categories'),    
    path('wishlist/', views.wishlist, name='wishlist'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('product_detail/', views.product_detail, name='product_detail'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
]