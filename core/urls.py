from django.urls import path
from .views import (
    home, products, plan, contact, join, login_view, 
    logout_view, dashboard, team, wallet, request_withdrawal, update_profile,
    purchase_product, admin_login, admin_dashboard, admin_users, admin_withdrawal_action,
    admin_settings, admin_homepage, admin_products, admin_product_create, admin_product_edit, admin_product_delete,
    admin_plans, admin_plan_create, admin_plan_edit, admin_plan_delete
)

urlpatterns = [
    # Public Pages
    path('', home, name='home'),
    path('products/', products, name='products'),
    path('plan/', plan, name='plan'),
    path('contact/', contact, name='contact'),

    # Authentication
    path('signup/', join, name='signup'),
    path('join/', join, name='join'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Protected Pages
    path('dashboard/', dashboard, name='dashboard'),
    path('team/', team, name='team'),
    path('wallet/', wallet, name='wallet'),
    
    # Profile
    path('profile/update/', update_profile, name='update_profile'),
    
    # Withdrawal
    path('withdrawal/request/', request_withdrawal, name='request_withdrawal'),
    
    # Purchase
    path('purchase/', purchase_product, name='purchase_product'),
    
    # Admin (Custom MLM Admin - Different from Django's /admin/)
    path('mlm-admin/login/', admin_login, name='admin_login'),
    path('mlm-admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('mlm-admin/users/', admin_users, name='admin_users'),
    path('mlm-admin/settings/', admin_settings, name='admin_settings'),
    path('mlm-admin/homepage/', admin_homepage, name='admin_homepage'),
    path('mlm-admin/products/', admin_products, name='admin_products'),
    path('mlm-admin/products/new/', admin_product_create, name='admin_product_create'),
    path('mlm-admin/products/<int:item_id>/edit/', admin_product_edit, name='admin_product_edit'),
    path('mlm-admin/products/<int:item_id>/delete/', admin_product_delete, name='admin_product_delete'),
    path('mlm-admin/plans/', admin_plans, name='admin_plans'),
    path('mlm-admin/plans/new/', admin_plan_create, name='admin_plan_create'),
    path('mlm-admin/plans/<int:item_id>/edit/', admin_plan_edit, name='admin_plan_edit'),
    path('mlm-admin/plans/<int:item_id>/delete/', admin_plan_delete, name='admin_plan_delete'),
    path('mlm-admin/withdrawal/<int:withdrawal_id>/action/', admin_withdrawal_action, name='admin_withdrawal_action'),
]
