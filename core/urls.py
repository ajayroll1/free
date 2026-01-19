from django.urls import path
from .views import (
    home, products, plan, contact, join, login_view, 
    logout_view, dashboard, team, wallet, request_withdrawal, update_profile
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
]
