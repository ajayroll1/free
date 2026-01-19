from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from decimal import Decimal
import os
from .models import CustomUser, Purchase, Referral, Withdrawal

def home(request):
    return render(request, 'home.html')

def products(request):
    return render(request, 'products.html')

def plan(request):
    return render(request, 'plan.html')

def contact(request):
    return render(request, 'contact.html')

@require_http_methods(["GET", "POST"])
@csrf_protect
def join(request):
    """User Registration View"""
    if request.method == 'POST':
        # Get form data
        sponsor_id = request.POST.get('sponsor_id', '').strip()
        sponsor_name = request.POST.get('sponsor_name', '').strip()
        first_name = request.POST.get('full_name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        errors = []
        
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            errors.append("Email already registered! Please login instead.")
        
        if CustomUser.objects.filter(mobile=mobile).exists():
            errors.append("Mobile number already registered!")
        
        # Password validation
        if password != confirm_password:
            errors.append("Passwords do not match!")
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long!")
        
        if not any(char.isupper() for char in password):
            errors.append("Password must contain at least one uppercase letter!")
        
        if not any(char.isdigit() for char in password):
            errors.append("Password must contain at least one digit!")
        
        if not sponsor_id or not sponsor_name or not first_name or not mobile or not email:
            errors.append("All fields are required!")
        
        # If there are errors, show them
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'loginSignup.html')
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=first_name,
                mobile=mobile,
                sponsor_id=sponsor_id,
                sponsor_name=sponsor_name,
                is_active_member=True
            )
            # Generate unique referral ID
            user.referral_id = user.generate_referral_id()
            user.save()
            
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'loginSignup.html')
    
    return render(request, 'loginSignup.html')

@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    """User Login View"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember')
        
        # Validation
        if not email or not password:
            messages.error(request, "Please provide both email and password!")
            return render(request, 'loginSignup.html')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Remember me functionality
            if not remember_me:
                request.session.set_expiry(0)  # Session expires on browser close
            
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password!")
            return render(request, 'loginSignup.html')
    
    return render(request, 'loginSignup.html')

@login_required(login_url='login')
def logout_view(request):
    """User Logout View"""
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('home')

@login_required(login_url='login')
def dashboard(request):
    """User Dashboard"""
    user = request.user
    
    # Get statistics
    referral_count = user.get_referral_count()
    purchase_count = user.get_purchase_count()
    total_spent = user.get_total_purchase_amount()
    
    # Get related data
    purchases = Purchase.objects.filter(user=user).order_by('-purchase_date')[:5]
    referrals = Referral.objects.filter(sponsor=user).select_related('referred_user')
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-requested_date')
    
    context = {
        'user': user,
        'referral_count': referral_count,
        'purchase_count': purchase_count,
        'total_spent': total_spent,
        'purchases': purchases,
        'referrals': referrals,
        'withdrawals': withdrawals,
    }
    return render(request, 'user/dashboard.html', context)

@login_required(login_url='login')
@require_http_methods(["POST"])
@csrf_protect
def request_withdrawal(request):
    """Handle Withdrawal Request"""
    user = request.user
    amount_str = request.POST.get('amount', '0').strip()
    
    try:
        amount = Decimal(amount_str)
    except:
        messages.error(request, "Invalid amount entered!")
        return redirect('dashboard')
    
    # Validation
    if amount <= 0:
        messages.error(request, "Amount must be greater than 0!")
        return redirect('dashboard')
    
    if amount > user.account_balance:
        messages.error(request, "Insufficient balance! Available: ₹" + str(user.account_balance))
        return redirect('dashboard')
    
    # Create withdrawal request
    try:
        withdrawal = Withdrawal.objects.create(
            user=user,
            amount=amount
        )
        
        # Deduct from account balance
        user.account_balance -= amount
        user.save()
        
        messages.success(
            request, 
            f"Withdrawal request submitted! Amount: ₹{amount}, Admin Charge (10%): ₹{withdrawal.admin_charge}, Net Amount: ₹{withdrawal.net_amount}"
        )
    except Exception as e:
        messages.error(request, f"Error processing withdrawal: {str(e)}")
    
    return redirect('dashboard')

@login_required(login_url='login')
def team(request):
    """Team Management"""
    return render(request, 'team.html')

@login_required(login_url='login')
def wallet(request):
    """Wallet/Balance Page"""
    return render(request, 'wallet.html')

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
@csrf_protect
def update_profile(request):
    """Update User Profile - Photo and Info"""
    user = request.user
    
    if request.method == 'POST':
        # Update profile photo if provided
        if 'profile_photo' in request.FILES:
            # Delete old photo if exists
            if user.profile_photo:
                old_photo_path = user.profile_photo.path
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)
            
            user.profile_photo = request.FILES['profile_photo']
            messages.success(request, "Profile photo updated successfully!")
        
        # Update user information
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Validate email uniqueness (if changed)
        if email and email != user.email:
            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "Email already exists! Please use a different email.")
                return redirect('dashboard')
            user.email = email
            user.username = email  # Update username to match email
        
        # Update other fields
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if mobile:
            # Check mobile uniqueness if changed
            if mobile != user.mobile:
                if CustomUser.objects.filter(mobile=mobile).exclude(id=user.id).exists():
                    messages.error(request, "Mobile number already exists!")
                    return redirect('dashboard')
            user.mobile = mobile
        
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('dashboard')
    
    # GET request - show profile edit form (handled in dashboard)
    return redirect('dashboard')
