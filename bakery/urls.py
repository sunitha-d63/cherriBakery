from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name='login'), 
    path('registration/login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.all_products, name='all_products'),
    path('products/<slug:slug>/', views.category_products, name='category_products'),
    path('products/<slug:category_slug>/<int:product_id>/', 
         views.product_detail, name='product_detail'),
    path('payment/', views.payment_page, name='payment_page'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('order-confirmation/', views.order_confirmation, name='order_confirmation'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('cart/', views.cart_page, name='cart_page'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("search/", views.search_products, name="search_products"),
]