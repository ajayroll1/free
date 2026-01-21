from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('plan/', views.plan, name='plan'),
    path('contact/', views.contact, name='contact'),

    # Auth
    path('signup/', views.join, name='signup'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User
    path('dashboard/', views.dashboard, name='dashboard'),
    path('team/', views.team, name='team'),
    path('wallet/', views.wallet, name='wallet'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('withdrawal/request/', views.request_withdrawal, name='request_withdrawal'),
    path('purchase/', views.purchase_product, name='purchase_product'),

    # Custom MLM Admin
    path('mlm-admin/login/', views.admin_login, name='admin_login'),
    path('mlm-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('mlm-admin/users/', views.admin_users, name='admin_users'),
   

    # path('mlm-admin/products/', views.admin_products, name='admin_products'),
    # path('mlm-admin/products/new/', views.admin_product_create, name='admin_product_create'),
    # path('mlm-admin/products/<int:item_id>/edit/', views.admin_product_edit, name='admin_product_edit'),
    # path('mlm-admin/products/<int:item_id>/delete/', views.admin_product_delete, name='admin_product_delete'),

    # path('mlm-admin/plans/', views.admin_plans, name='admin_plans'),
    # path('mlm-admin/plans/new/', views.admin_plan_create, name='admin_plan_create'),
    # path('mlm-admin/plans/<int:item_id>/edit/', views.admin_plan_edit, name='admin_plan_edit'),
    # path('mlm-admin/plans/<int:item_id>/delete/', views.admin_plan_delete, name='admin_plan_delete'),

    path(
        'mlm-admin/withdrawal/<int:withdrawal_id>/action/',
        views.admin_withdrawal_action,
        name='admin_withdrawal_action'
    ),
]
