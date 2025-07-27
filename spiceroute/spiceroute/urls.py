"""
URL configuration for spiceroute project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt # For API endpoint simplicity in hackathon


urlpatterns = [
    path('admin/', admin.site.urls), # <--- THIS LINE IS CRUCIAL FOR ADMIN ACCESS
    # path('', include('spiceroute_app.urls')),
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about_view, name='about'),
    path('faq/', views.faq_view, name='faq'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),

    # Vendor-specific URLs
    path('vendor/dashboard/', views.vendor_dashboard_view, name='vendor_dashboard'),
    path('vendor/browse/', views.browse_products_view, name='browse_products'),
    path('vendor/checkout/', views.checkout_view, name='checkout'),
    path('vendor/orders/', views.vendor_orders_view, name='vendor_orders'),
    path('vendor/loans/', views.vendor_loans_view, name='vendor_loans'),
    path('vendor/leftovers/', views.vendor_leftovers_view, name='vendor_leftovers'),
    path('vendor/leftovers/mark-sold/<int:listing_id>/', views.mark_leftover_as_sold_view, name='mark_leftover_as_sold'),
    path('vendor/my-reviews/', views.vendor_my_reviews_view, name='vendor_my_reviews'),

    # Supplier-specific URLs
    path('supplier/dashboard/', views.supplier_dashboard_view, name='supplier_dashboard'),
    path('supplier/orders/', views.supplier_orders_view, name='supplier_orders'),
    path('supplier/inventory/', views.supplier_inventory_view, name='supplier_inventory'),
    path('supplier/upstream-suppliers/', views.supplier_upstream_suppliers_view, name='supplier_upstream_suppliers'),
    path('supplier/financials/', views.financials_view, name='supplier_financials'),
    path('supplier/profile/', views.supplier_profile_view, name='supplier_profile'),

    # API Endpoints (for AJAX/JS requests)
    path('api/order-details/<int:order_id>/', views.order_details_api_view, name='order_details_api'),
    path('api/product-details/<int:product_id>/', views.product_details_api_view, name='product_details_api'),
    path('api/update-product-price/<int:product_id>/', views.update_product_price_api_view, name='update_product_price_api'), # NEW
    path('api/add-ai-suggestion-to-cart/', views.add_ai_suggestion_to_cart_api_view, name='add_ai_suggestion_to_cart_api'), # NEW
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)