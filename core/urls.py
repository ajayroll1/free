from django.urls import path
from .views import home, products, plan, contact, join, login_view, dashboard, team, wallet

urlpatterns = [
    path('', home, name='home'),
    path('products/', products, name='products'),
    path('plan/', plan, name='plan'),
    path('contact/', contact, name='contact'),

    path('join/', join, name='join'),
    path('login/', login_view, name='login'),

    path('dashboard/', dashboard, name='dashboard'),
    path('team/', team, name='team'),
    path('wallet/', wallet, name='wallet'),
]
