from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
import os
from .models import (
    CustomUser, Purchase, Referral, Withdrawal, Product, 
    ReferralSettings, HomePageSection, PlanItem, ProductItem
)
from .forms import HomePageSectionForm, ProductItemForm, PlanItemForm

def home(request):
    # Get dynamic sections
    sections = HomePageSection.objects.filter(is_active=True)
    plan_items = PlanItem.objects.filter(is_active=True)
    product_items = ProductItem.objects.filter(is_active=True)
    
    context = {
        'sections': {s.section_type: s for s in sections},
        'plan_items': plan_items,
        'product_items': product_items,
    }
    return render(request, 'home.html', context)

def products(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

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
            
            # Create referral record if sponsor exists
            if sponsor_id:
                try:
                    sponsor = CustomUser.objects.get(referral_id=sponsor_id)
                    referral_settings = ReferralSettings.objects.filter(is_active=True).first()
                    if referral_settings:
                        commission = referral_settings.direct_referral_amount
                    else:
                        commission = Decimal('200.00')
                    
                    Referral.objects.create(
                        sponsor=sponsor,
                        referred_user=user,
                        commission_earned=commission
                    )
                    # Add commission to sponsor's account
                    sponsor.account_balance += commission
                    sponsor.save()
                except CustomUser.DoesNotExist:
                    pass
            
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
    
    # Get total referral earnings
    total_referral_earnings = Decimal('0.00')
    referrals = Referral.objects.filter(sponsor=user)
    for ref in referrals:
        total_referral_earnings += ref.commission_earned
    
    # Get related data
    purchases = Purchase.objects.filter(user=user).order_by('-purchase_date')
    referrals = Referral.objects.filter(sponsor=user).select_related('referred_user')
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-requested_date')
    
    context = {
        'user': user,
        'referral_count': referral_count,
        'purchase_count': purchase_count,
        'total_spent': total_spent,
        'total_referral_earnings': total_referral_earnings,
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

@login_required(login_url='login')
@require_http_methods(["POST"])
@csrf_protect
def purchase_product(request):
    """Handle Product Purchase"""
    user = request.user
    
    product_name = request.POST.get('product_name', '').strip()
    product_price = request.POST.get('product_price', '0').strip()
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        price = Decimal(product_price.replace('₹', '').replace(',', ''))
        total_amount = price * quantity
        
        # Get or create product
        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                'price': price,
                'description': f'Purchase of {product_name}'
            }
        )
        
        # Create purchase record
        purchase = Purchase.objects.create(
            user=user,
            product=product,
            quantity=quantity,
            total_amount=total_amount
        )
        
        messages.success(
            request,
            f"Purchase successful! Product: {product_name}, Quantity: {quantity}, Total: ₹{total_amount}"
        )
        return JsonResponse({
            'success': True,
            'message': 'Purchase completed successfully!'
        })
        
    except Exception as e:
        messages.error(request, f"Error processing purchase: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

# ========== ADMIN DASHBOARD VIEWS ==========

def admin_login(request):
    """Admin Login View - Custom MLM Admin Login"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, "Please provide both email and password!")
            return render(request, 'admin/login.html')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid email or password!")
            return render(request, 'admin/login.html')
    
    # GET request - show custom login page
    return render(request, 'admin/login.html')

def admin_dashboard(request):
    """Admin Dashboard"""
    
    # Get statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active_member=True).count()
    total_withdrawals = Withdrawal.objects.count()
    pending_withdrawals = Withdrawal.objects.filter(status='pending').count()
    total_purchases = Purchase.objects.count()
    total_referrals = Referral.objects.count()
    
    # -------- Table Search + Pagination (server-side) --------
    # Query params (separate for each table so they don't conflict)
    withdrawals_q = (request.GET.get('withdrawals_q') or '').strip()
    users_q = (request.GET.get('users_q') or '').strip()
    purchases_q = (request.GET.get('purchases_q') or '').strip()

    withdrawals_page_number = request.GET.get('withdrawals_page') or 1
    users_page_number = request.GET.get('users_page') or 1
    purchases_page_number = request.GET.get('purchases_page') or 1

    # Pending Withdrawals (table)
    pending_withdrawals_qs = Withdrawal.objects.filter(status='pending').select_related('user').order_by('-requested_date')
    if withdrawals_q:
        pending_withdrawals_qs = pending_withdrawals_qs.filter(
            Q(user__first_name__icontains=withdrawals_q)
            | Q(user__last_name__icontains=withdrawals_q)
            | Q(user__email__icontains=withdrawals_q)
            | Q(user__mobile__icontains=withdrawals_q)
        )
    pending_withdrawals_paginator = Paginator(pending_withdrawals_qs, 10)
    pending_withdrawal_requests = pending_withdrawals_paginator.get_page(withdrawals_page_number)

    # Recent Users (table)
    recent_users_qs = CustomUser.objects.order_by('-created_at')
    if users_q:
        recent_users_qs = recent_users_qs.filter(
            Q(first_name__icontains=users_q)
            | Q(last_name__icontains=users_q)
            | Q(email__icontains=users_q)
            | Q(mobile__icontains=users_q)
            | Q(referral_id__icontains=users_q)
        )
    recent_users_paginator = Paginator(recent_users_qs, 10)
    recent_users = recent_users_paginator.get_page(users_page_number)

    # Recent Purchases (table)
    recent_purchases_qs = Purchase.objects.select_related('user', 'product').order_by('-purchase_date')
    if purchases_q:
        recent_purchases_qs = recent_purchases_qs.filter(
            Q(user__first_name__icontains=purchases_q)
            | Q(user__last_name__icontains=purchases_q)
            | Q(user__email__icontains=purchases_q)
            | Q(product__name__icontains=purchases_q)
        )
    recent_purchases_paginator = Paginator(recent_purchases_qs, 10)
    recent_purchases = recent_purchases_paginator.get_page(purchases_page_number)
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_withdrawals': total_withdrawals,
        'pending_withdrawals': pending_withdrawals,
        'total_purchases': total_purchases,
        'total_referrals': total_referrals,
        'recent_users': recent_users,
        'pending_withdrawal_requests': pending_withdrawal_requests,
        'recent_purchases': recent_purchases,
        'withdrawals_q': withdrawals_q,
        'users_q': users_q,
        'purchases_q': purchases_q,
    }
    return render(request, 'admin/admin_dashboard.html', context)

def admin_users(request):
    """Admin - User Management - Fetch all users from database (search + pagination)"""

    q = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page') or 1

    users_qs = CustomUser.objects.all().order_by('-created_at')
    if q:
        users_qs = users_qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(mobile__icontains=q)
            | Q(referral_id__icontains=q)
            | Q(sponsor_id__icontains=q)
            | Q(sponsor_name__icontains=q)
        )

    paginator = Paginator(users_qs, 10)
    users_page = paginator.get_page(page_number)

    return render(
        request,
        'admin/admin_users.html',
        {
            'users': users_page,   # keep template variable name stable
            'q': q,
        },
    )


def admin_settings(request):
    """Admin Settings (placeholder page)"""
    return render(request, 'admin/admin_settings.html')


def admin_homepage(request):
    """Admin - Home Page settings (manage section titles/subtitles)"""
    # Ensure products section exists
    products_section, _ = HomePageSection.objects.get_or_create(
        section_type='products',
        defaults={'title': 'Our Premium Kits & Packages', 'subtitle': 'Quality products at affordable prices', 'is_active': True, 'display_order': 0},
    )

    form = HomePageSectionForm(instance=products_section)
    if request.method == 'POST':
        form = HomePageSectionForm(request.POST, instance=products_section)
        if form.is_valid():
            form.save()
            messages.success(request, "Home page products section updated.")
            return redirect('admin_homepage')

    return render(
        request,
        'admin/admin_homepage.html',
        {
            'products_section': products_section,
            'form': form,
        },
    )


def admin_products(request):
    """Admin - Manage home page product cards (CRUD for ProductItem)"""
    q = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page') or 1

    items_qs = ProductItem.objects.all().order_by('display_order', '-id')
    if q:
        items_qs = items_qs.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
        )

    paginator = Paginator(items_qs, 10)
    items_page = paginator.get_page(page_number)

    return render(
        request,
        'admin/admin_products.html',
        {
            'items': items_page,
            'q': q,
        },
    )


def admin_plans(request):
    """Admin - Manage business plan cards (PlanItem)"""
    q = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page') or 1

    plans_qs = PlanItem.objects.all().order_by('display_order', '-id')
    if q:
        plans_qs = plans_qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(amount__icontains=q)
        )

    paginator = Paginator(plans_qs, 10)
    plans_page = paginator.get_page(page_number)

    return render(
        request,
        'admin/admin_plans.html',
        {
            'items': plans_page,
            'q': q,
        },
    )


@csrf_protect
def admin_product_create(request):
    """Admin - Create ProductItem"""
    form = ProductItemForm()
    if request.method == 'POST':
        form = ProductItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            # attach to products section by default
            products_section, _ = HomePageSection.objects.get_or_create(
                section_type='products',
                defaults={'title': 'Our Premium Kits & Packages', 'subtitle': 'Quality products at affordable prices', 'is_active': True, 'display_order': 0},
            )
            item.section = products_section
            item.save()
            messages.success(request, "Product card created.")
            return redirect('admin_products')

    return render(request, 'admin/admin_product_form.html', {'form': form, 'mode': 'create'})


@csrf_protect
def admin_plan_create(request):
    """Admin - Create PlanItem"""
    form = PlanItemForm()
    if request.method == 'POST':
        form = PlanItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            plans_section, _ = HomePageSection.objects.get_or_create(
                section_type='plans',
                defaults={'title': 'Business Plans', 'subtitle': 'Multiple ways to earn with our proven system', 'is_active': True, 'display_order': 0},
            )
            item.section = plans_section
            item.save()
            messages.success(request, "Business plan card created.")
            return redirect('admin_plans')

    return render(request, 'admin/admin_plan_form.html', {'form': form, 'mode': 'create'})


@csrf_protect
def admin_product_edit(request, item_id):
    """Admin - Edit ProductItem"""
    item = get_object_or_404(ProductItem, id=item_id)
    form = ProductItemForm(instance=item)
    if request.method == 'POST':
        form = ProductItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Product card updated.")
            return redirect('admin_products')

    return render(request, 'admin/admin_product_form.html', {'form': form, 'mode': 'edit', 'item': item})


@csrf_protect
def admin_plan_edit(request, item_id):
    """Admin - Edit PlanItem"""
    item = get_object_or_404(PlanItem, id=item_id)
    form = PlanItemForm(instance=item)
    if request.method == 'POST':
        form = PlanItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Business plan card updated.")
            return redirect('admin_plans')

    return render(request, 'admin/admin_plan_form.html', {'form': form, 'mode': 'edit', 'item': item})


@require_http_methods(["POST"])
@csrf_protect
def admin_product_delete(request, item_id):
    """Admin - Delete ProductItem"""
    item = get_object_or_404(ProductItem, id=item_id)
    item.delete()
    messages.success(request, "Product card deleted.")
    return redirect('admin_products')


@require_http_methods(["POST"])
@csrf_protect
def admin_plan_delete(request, item_id):
    """Admin - Delete PlanItem"""
    item = get_object_or_404(PlanItem, id=item_id)
    item.delete()
    messages.success(request, "Business plan card deleted.")
    return redirect('admin_plans')

@login_required(login_url='admin_login')
@require_http_methods(["POST"])
@csrf_protect
def admin_withdrawal_action(request, withdrawal_id):
    """Admin - Approve/Reject Withdrawal"""
    
    withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')
    
    if action == 'approve':
        withdrawal.status = 'approved'
        messages.success(request, f"Withdrawal request approved for ₹{withdrawal.amount}")
    elif action == 'reject':
        withdrawal.status = 'rejected'
        # Refund amount back to user
        withdrawal.user.account_balance += withdrawal.amount
        withdrawal.user.save()
        messages.success(request, f"Withdrawal request rejected. Amount refunded.")
    elif action == 'complete':
        withdrawal.status = 'completed'
        withdrawal.processed_date = timezone.now()
        messages.success(request, f"Withdrawal marked as completed.")
    
    if notes:
        withdrawal.notes = notes
    withdrawal.save()
    
    return redirect('admin_dashboard')
