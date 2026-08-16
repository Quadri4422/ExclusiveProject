import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)


def login_view(request):
    # If user is already authenticated, redirect to mainsite home
    if request.user.is_authenticated:
        return redirect('mainsite:index')

    if request.method == 'POST':
        identifier = request.POST.get('email_or_phone', '').strip()
        password = request.POST.get('password', '').strip()

        if not identifier or not password:
            messages.error(request, 'Please provide both your credential and password.')
            return render(request, 'account/login.html')

        # Find user matching username or email
        user_obj = User.objects.filter(
            Q(username__iexact=identifier) | 
            Q(email__iexact=identifier)
        ).first()

        username = user_obj.username if user_obj else identifier

        # Authenticate user credentials
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Safely redirect to 'next' parameter if present, otherwise mainsite index
                next_url = request.GET.get('next', '')
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url, 
                    allowed_hosts={request.get_host()}
                ):
                    return redirect(next_url)
                
                return redirect('mainsite:index')
            else:
                messages.error(request, 'Your account is currently disabled.')
        else:
            messages.error(request, 'Invalid email/phone or password.')

    return render(request, 'account/login.html')


def signup_view(request):
    # If user is already authenticated, redirect to mainsite home
    if request.user.is_authenticated:
        return redirect('mainsite:index')

    if request.method == 'POST':
        full_name = request.POST.get('name', '').strip()
        email_or_phone = request.POST.get('email_or_phone', '').strip()
        password = request.POST.get('password', '').strip()

        # Input validation
        if not full_name or not email_or_phone or not password:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'account/signup.html')

        # Split full name into first and last name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Determine if input is email or phone number
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        is_email = bool(re.match(email_pattern, email_or_phone))

        email = email_or_phone if is_email else ''
        username = email_or_phone.lower()

        # Check for existing account
        if User.objects.filter(username=username).exists() or (email and User.objects.filter(email=email).exists()):
            messages.error(request, 'An account with this email or phone number already exists.')
            return render(request, 'account/signup.html')

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Auto-login after successful registration
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome to Exclusive, {first_name}!')
            return redirect('mainsite:index')

        except Exception:
            messages.error(request, 'An error occurred during account creation. Please try again.')

    return render(request, 'account/signup.html')


def logout_view(request):
    """Logs out the user and redirects to the login page."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('account:login')



class CustomPasswordResetView(PasswordResetView):
    template_name = 'account/password_reset_form.html'
    email_template_name = 'account/password_reset_email.html'
    subject_template_name = 'account/password_reset_subject.txt'
    success_url = reverse_lazy('account:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'account/password_reset_complete.html'