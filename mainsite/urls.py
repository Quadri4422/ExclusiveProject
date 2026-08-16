from django.urls import path
from . import views

app_name = 'mainsite'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Categories Routes
    path('categories/', views.categories, name='categories'),
    path('categories/<slug:slug>/', views.categories, name='category_detail'),
    
    # Product Detail
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Cart Routes
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Wishlist Routes
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-all/', views.move_all_to_bag, name='move_all_to_bag'),
    
    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('order/success/<int:order_id>/', views.order_success_view, name='order_success'),

    # Content Pages
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about, name='about'),

    # User Account & Settings
    path('profile/', views.profile, name='profile'),
    path('address-book/', views.address_book_view, name='address_book'),
    path('address-book/delete/<int:address_id>/', views.delete_address_view, name='delete_address'),
    
    path('payment-options/', views.payment_options_view, name='payment_options'),
    path('payment-options/delete/<int:payment_id>/', views.delete_payment_view, name='delete_payment'),
    
    path('returns/', views.returns_view, name='returns'),
    path('cancellations/', views.cancellations_view, name='cancellations'),

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use_view, name='terms_of_use'),
    path('faq/', views.faq_view, name='faq'),
]