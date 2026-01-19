from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def products(request):
    return render(request, 'products.html')

def plan(request):
    return render(request, 'plan.html')

def contact(request):
    return render(request, 'contact.html')

def join(request):
    return render(request, 'join.html')

def login_view(request):
    return render(request, 'login.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def team(request):
    return render(request, 'team.html')

def wallet(request):
    return render(request, 'wallet.html')
