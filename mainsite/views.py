from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'mainsite/index.html')

def categories(request):
    return render(request, 'mainsite/categories.html')

def wishlist(request):
    return render(request, 'mainsite/wishlist.html')

def cart(request):
    return render(request, 'mainsite/cart.html')

def checkout(request):
    return render(request, 'mainsite/checkout.html')

def product_detail(request):
    return render(request, 'mainsite/product_detail.html')

def contact(request):
    return render(request, 'mainsite/contact.html')

def about(request): 
    return render(request, 'mainsite/about.html')

def profile(request):
    return render(request, 'mainsite/profile.html')