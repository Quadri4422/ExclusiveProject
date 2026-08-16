from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.db import transaction

from .forms import CheckoutForm
from .models import (
    Category,
    Product,
    Profile,
    Address,
    PaymentOption,
    Order,
    OrderReturn,
    OrderCancellation,
    OrderItem,
    Coupon,
    Cart,
    CartItem,
    ContactMessage
)

User = get_user_model()


# ==========================================
# PUBLIC / CATALOG VIEWS
# ==========================================

def index(request):
    """Home page displaying categories and featured product sections."""
    categories = Category.objects.all()

    base_products = (
        Product.objects.filter(is_active=True)
        .select_related('category')
        .prefetch_related('images')
    )

    flash_sales_products = base_products.filter(flashsales=True)[:8]
    best_selling_products = base_products.filter(best_selling_products=True)[:8]
    explore_products = base_products.filter(explore_our_products=True)[:8]

    context = {
        'categories': categories,
        'flash_sales_products': flash_sales_products,
        'best_selling_products': best_selling_products,
        'explore_our_products': explore_products,
    }
    return render(request, 'mainsite/index.html', context)


def categories(request, slug=None):
    """Category listing and filtering view."""
    categories_list = Category.objects.all()
    selected_category_obj = None

    products = (
        Product.objects.filter(is_active=True)
        .select_related('category')
        .prefetch_related('images')
    )

    if slug:
        selected_category_obj = get_object_or_404(Category, slug=slug)
        products = products.filter(category=selected_category_obj)

    context = {
        'categories': categories_list,
        'products': products,
        'selected_category': slug,
        'selected_category_obj': selected_category_obj,
    }
    return render(request, 'mainsite/categories.html', context)


def product_detail(request, slug):
    """Product detail view with related category recommendations."""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'), 
        slug=slug, 
        is_active=True
    )

    related_products = []
    if product.category:
        related_products = (
            Product.objects.filter(category=product.category, is_active=True)
            .exclude(id=product.id)
            .select_related('category')
            .prefetch_related('images')[:4]
        )

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'mainsite/product_detail.html', context)


# ==========================================
# WISHLIST VIEWS (Session-based)
# ==========================================

@login_required
def wishlist_view(request):
    """User Wishlist Display View."""
    wishlist_ids = request.session.get('wishlist', [])
    
    clean_ids = []
    for i in wishlist_ids:
        try:
            clean_ids.append(int(i))
        except (ValueError, TypeError):
            continue

    wishlist_products = Product.objects.filter(id__in=clean_ids, is_active=True).select_related('category').prefetch_related('images')

    context = {
        'wishlist_products': wishlist_products,
    }
    return render(request, 'mainsite/wishlist.html', context)


@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """Add product to session wishlist via AJAX or standard POST."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    wishlist = request.session.get('wishlist', [])
    if not isinstance(wishlist, list):
        wishlist = []

    clean_wishlist = []
    for i in wishlist:
        try:
            clean_wishlist.append(int(i))
        except (ValueError, TypeError):
            continue

    target_id = int(product_id)
    added = False

    if target_id not in clean_wishlist:
        clean_wishlist.append(target_id)
        request.session['wishlist'] = clean_wishlist
        request.session.modified = True
        added = True
        msg = f"{product.name} added to your wishlist!"
    else:
        msg = f"{product.name} is already in your wishlist."

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
        'application/json' in (request.content_type or '')
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'added': added,
            'wishlist_count': len(clean_wishlist),
            'message': msg
        })

    messages.success(request, msg)
    return redirect('mainsite:wishlist')


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """Remove product from session wishlist."""
    wishlist_ids = request.session.get('wishlist', [])
    if not isinstance(wishlist_ids, list):
        wishlist_ids = []

    clean_ids = []
    for i in wishlist_ids:
        try:
            clean_ids.append(int(i))
        except (ValueError, TypeError):
            continue

    try:
        target_id = int(product_id)
    except (ValueError, TypeError):
        target_id = None

    if target_id in clean_ids:
        clean_ids.remove(target_id)
        request.session['wishlist'] = clean_ids
        request.session.modified = True
        messages.success(request, "Product removed from your wishlist.")

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
        'application/json' in (request.content_type or '')
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'wishlist_count': len(clean_ids)
        })

    return redirect('mainsite:wishlist')


@login_required
@require_POST
def move_all_to_bag(request):
    """Move all session wishlist products into the user's session cart and redirect to cart."""
    wishlist_ids = request.session.get('wishlist', [])
    
    if wishlist_ids:
        cart_data = request.session.get('cart', {})
        if not isinstance(cart_data, dict):
            cart_data = {}
        
        products = Product.objects.filter(id__in=wishlist_ids, is_active=True)
        
        for product in products:
            str_id = str(product.id)
            cart_data[str_id] = cart_data.get(str_id, 0) + 1
                
        request.session['cart'] = cart_data
        request.session['wishlist'] = []
        request.session.modified = True

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success', 
            'redirect_url': '/cart/'
        })

    return redirect('mainsite:cart')


# ==========================================
# CART VIEWS
# ==========================================

def _get_cart_details(session_cart):
    """Helper utility to calculate cart items, total price, and item count using Decimal precision,
    while automatically cleaning up invalid or inactive products from the session."""
    cart_items = []
    total_price = Decimal('0.00')
    total_count = 0

    if isinstance(session_cart, dict) and session_cart:
        product_ids = [int(pid) for pid in session_cart.keys() if str(pid).isdigit()]
        products = (
            Product.objects.filter(id__in=product_ids, is_active=True)
            .select_related('category')
            .prefetch_related('images')
        )

        updated_session_cart = {}

        for product in products:
            str_id = str(product.id)
            raw_qty = session_cart.get(str_id, session_cart.get(product.id, 0))
            try:
                quantity = max(1, int(raw_qty))
            except (ValueError, TypeError):
                quantity = 1

            if product.discount_price and product.discount_price < product.price:
                effective_price = Decimal(str(product.discount_price))
            else:
                effective_price = Decimal(str(product.price))

            subtotal = (effective_price * quantity).quantize(Decimal('0.01'))
            total_price += subtotal
            total_count += quantity

            cart_items.append({
                'product': product,
                'quantity': quantity,
                'effective_price': effective_price,
                'subtotal': subtotal,
            })
            
            updated_session_cart[str_id] = quantity

        # Clean stale/inactive products out of the session cart dictionary
        if len(updated_session_cart) != len(session_cart):
            session_cart.clear()
            session_cart.update(updated_session_cart)

    return cart_items, total_price.quantize(Decimal('0.01')), total_count


def cart(request):
    """Shopping Cart Display View."""
    session_cart = request.session.get('cart', {})
    cart_items, total_price, total_count = _get_cart_details(session_cart)
    request.session.modified = True  # Ensure session cleanup changes persist

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_item_count': total_count,
    }
    return render(request, 'mainsite/cart.html', context)


@require_POST
def add_to_cart(request, product_id):
    """Add product to session cart."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart_data = request.session.get('cart', {})
    if not isinstance(cart_data, dict):
        cart_data = {}

    str_id = str(product_id)
    content_type = request.content_type or ''

    quantity = None
    if 'application/json' in content_type:
        try:
            body = json.loads(request.body)
            quantity = body.get('quantity')
        except (json.JSONDecodeError, TypeError):
            pass

    if quantity is None:
        quantity = request.POST.get('quantity', 1)

    try:
        quantity = max(1, int(quantity))
    except (ValueError, TypeError):
        quantity = 1

    cart_data[str_id] = cart_data.get(str_id, 0) + quantity
    request.session['cart'] = cart_data
    request.session.modified = True

    _, total_price, total_count = _get_cart_details(cart_data)

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
        'application/json' in content_type
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'message': f'{product.name} added to cart',
            'cart_count': total_count,
            'total_price': float(total_price),
        })

    messages.success(request, f"{product.name} added to your cart.")
    return redirect('mainsite:cart')


@require_POST
def update_cart(request, product_id):
    """Update quantity of an item in session cart."""
    cart_data = request.session.get('cart', {})
    if not isinstance(cart_data, dict):
        cart_data = {}

    str_id = str(product_id)
    int_id = int(product_id) if str(product_id).isdigit() else product_id

    content_type = request.content_type or ''
    quantity = None

    if 'application/json' in content_type:
        try:
            body = json.loads(request.body)
            quantity = body.get('quantity')
        except (json.JSONDecodeError, TypeError):
            pass

    if quantity is None:
        quantity = request.POST.get('quantity')

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1

    target_key = str_id if str_id in cart_data else (int_id if int_id in cart_data else str_id)

    if quantity > 0:
        cart_data[target_key] = quantity
    else:
        cart_data.pop(target_key, None)

    request.session['cart'] = cart_data
    request.session.modified = True

    cart_items, total_price, total_count = _get_cart_details(cart_data)
    item_subtotal = next(
        (item['subtotal'] for item in cart_items if str(item['product'].id) == str_id), 
        Decimal('0.00')
    )

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
        'application/json' in content_type
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'cart_count': total_count,
            'subtotal': float(item_subtotal),
            'total_price': float(total_price),
        })

    return redirect('mainsite:cart')


@require_POST
def remove_from_cart(request, product_id):
    """Remove item completely from session cart."""
    cart_data = request.session.get('cart', {})
    if not isinstance(cart_data, dict):
        cart_data = {}

    str_id = str(product_id)
    int_id = int(product_id) if str(product_id).isdigit() else product_id

    removed = False
    if str_id in cart_data:
        del cart_data[str_id]
        removed = True
    if int_id in cart_data:
        del cart_data[int_id]
        removed = True

    if removed:
        request.session['cart'] = cart_data
        request.session.modified = True

    _, total_price, total_count = _get_cart_details(cart_data)

    content_type = request.content_type or ''
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
        'application/json' in content_type
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'cart_count': total_count,
            'total_price': float(total_price),
        })

    return redirect('mainsite:cart')


# ==========================================
# CHECKOUT & COUPON VIEWS
# ==========================================

@login_required
def checkout(request):
    """Unified Checkout View supporting both form processing and order creation."""
    session_cart = request.session.get('cart', {})
    cart_items, subtotal, total_count = _get_cart_details(session_cart)

    if not cart_items:
        messages.warning(request, "Your cart is empty. Add items before checking out.")
        return redirect('mainsite:cart')

    shipping = Decimal('0.00')
    discount = Decimal('0.00')
    coupon_id = request.session.get('coupon_id')

    if coupon_id:
        now = timezone.now()
        try:
            coupon = Coupon.objects.get(
                id=coupon_id, 
                active=True, 
                valid_from__lte=now, 
                valid_to__gte=now
            )
            discount = (subtotal * Decimal(str(coupon.discount_percent)) / Decimal('100')).quantize(Decimal('0.01'))
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None

    total = max(Decimal('0.00'), (subtotal + shipping - discount)).quantize(Decimal('0.01'))

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first() or addresses.first()
    payment_options = PaymentOption.objects.filter(user=request.user)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.subtotal = subtotal
                order.shipping_cost = shipping
                order.discount_amount = discount
                order.total_amount = total
                order.save()

                order_items_to_create = [
                    OrderItem(
                        order=order,
                        product=item['product'],
                        price=item['effective_price'],
                        quantity=item['quantity']
                    ) for item in cart_items
                ]
                OrderItem.objects.bulk_create(order_items_to_create)

                if form.cleaned_data.get('save_info'):
                    Address.objects.update_or_create(
                        user=request.user,
                        is_default=True,
                        defaults={
                            'full_name': f"{order.first_name} {getattr(order, 'last_name', '')}".strip(),
                            'phone': getattr(order, 'phone', ''),
                            'street_address': getattr(order, 'street_address', ''),
                            'city': getattr(order, 'city', ''),
                        }
                    )

            request.session['cart'] = {}
            request.session['coupon_id'] = None
            request.session.modified = True

            messages.success(request, f"Order #{order.id} placed successfully!")
            return redirect('mainsite:order_success', order_id=order.id)
        else:
            messages.error(request, "Please correct the errors in the checkout form below.")
    else:
        initial_data = {
            'first_name': request.user.first_name or request.user.username,
            'email': request.user.email,
        }
        if default_address:
            initial_data.update({
                'street_address': default_address.street_address,
                'city': default_address.city,
                'phone': default_address.phone,
            })
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'cart_item_count': total_count,
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'total_price': total,
        'addresses': addresses,
        'default_address': default_address,
        'payment_options': payment_options,
    }
    return render(request, 'mainsite/checkout.html', context)


@login_required
@require_POST
def apply_coupon_view(request):
    """Apply discount coupon code to current order session."""
    code = request.POST.get('coupon_code', '').strip()
    now = timezone.now()
    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True, valid_from__lte=now, valid_to__gte=now)
        request.session['coupon_id'] = coupon.id
        messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
    except Coupon.DoesNotExist:
        request.session['coupon_id'] = None
        messages.error(request, "Invalid or expired coupon code.")

    return redirect('mainsite:checkout')


@login_required
def order_success_view(request, order_id):
    """Order success confirmation page for the user who placed the order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order).select_related('product')

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'mainsite/order_success.html', context)


# ==========================================
# STATIC & CONTACT VIEWS
# ==========================================

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message_text = request.POST.get('message')

        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            message=message_text
        )

        messages.success(request, "Your message has been sent successfully! We will contact you within 24 hours.")
        return redirect('mainsite:contact')

    return render(request, 'mainsite/contact.html')


def about(request):
    """About Us Information Page."""
    return render(request, 'mainsite/about.html')


# ==========================================
# USER ACCOUNT MANAGEMENT VIEWS
# ==========================================

@login_required
def profile(request):
    """User Profile and Password Management View."""
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        if email and email != request.user.email:
            if User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
                messages.error(request, "This email address is already in use by another account.")
                return redirect('mainsite:profile')

        request.user.first_name = first_name
        request.user.last_name = last_name
        if email:
            request.user.email = email
        request.user.save()

        profile_obj.address = request.POST.get('address', '').strip()
        profile_obj.save()

        curr_pass = request.POST.get('current_password', '').strip()
        new_pass = request.POST.get('new_password', '').strip()
        conf_pass = request.POST.get('confirm_password', '').strip()

        password_changed = False
        password_error = False

        if curr_pass or new_pass or conf_pass:
            if not all([curr_pass, new_pass, conf_pass]):
                messages.error(request, 'Please fill in all password fields to update your password.')
                password_error = True
            elif not request.user.check_password(curr_pass):
                messages.error(request, 'Current password is incorrect.')
                password_error = True
            elif new_pass != conf_pass:
                messages.error(request, 'New passwords do not match.')
                password_error = True
            else:
                try:
                    validate_password(new_pass, user=request.user)
                    request.user.set_password(new_pass)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    password_changed = True
                except ValidationError as err:
                    for error in err.messages:
                        messages.error(request, error)
                    password_error = True

        if password_changed:
            messages.success(request, 'Profile details and password updated successfully!')
        elif not password_error:
            messages.success(request, 'Profile details updated!')

        return redirect('mainsite:profile')

    return render(request, 'mainsite/profile.html', {'profile': profile_obj, 'active_tab': 'profile'})


@login_required
def address_book_view(request):
    """User Address Book Management."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        street_address = request.POST.get('street_address', '').strip()

        if not full_name or not street_address:
            messages.error(request, 'Please fill in required address fields.')
            return redirect('mainsite:address_book')

        is_default = 'is_default' in request.POST

        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=request.POST.get('phone', '').strip(),
            street_address=street_address,
            city=request.POST.get('city', '').strip(),
            state=request.POST.get('state', '').strip(),
            postal_code=request.POST.get('postal_code', '').strip(),
            country=request.POST.get('country', 'United States').strip(),
            is_default=is_default
        )
        messages.success(request, 'New address added successfully!')
        return redirect('mainsite:address_book')

    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-id')
    return render(request, 'mainsite/address_book.html', {'addresses': addresses, 'active_tab': 'address_book'})


@login_required
@require_POST
def delete_address_view(request, address_id):
    """Delete address endpoint."""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully.')
    return redirect('mainsite:address_book')


@login_required
def payment_options_view(request):
    """User Saved Payment Methods."""
    if request.method == 'POST':
        card_holder = request.POST.get('card_holder_name', '').strip()
        card_num = request.POST.get('card_number', '').replace(' ', '')

        if not card_holder or not card_num:
            messages.error(request, 'Please provide card holder name and card number.')
            return redirect('mainsite:payment_options')

        last_four = card_num[-4:] if len(card_num) >= 4 else '0000'
        is_default = 'is_default' in request.POST

        if is_default:
            PaymentOption.objects.filter(user=request.user, is_default=True).update(is_default=False)

        current_year = timezone.now().year
        try:
            exp_month = int(request.POST.get('expiry_month', 1))
            exp_year = int(request.POST.get('expiry_year', current_year))
        except (ValueError, TypeError):
            exp_month = 1
            exp_year = current_year

        PaymentOption.objects.create(
            user=request.user,
            card_holder_name=card_holder,
            card_type=request.POST.get('card_type', 'visa'),
            last_four=last_four,
            expiry_month=exp_month,
            expiry_year=exp_year,
            is_default=is_default
        )
        messages.success(request, 'Payment method added successfully!')
        return redirect('mainsite:payment_options')

    payment_methods = PaymentOption.objects.filter(user=request.user).order_by('-is_default', '-id')
    return render(request, 'mainsite/payment_options.html', {'payment_methods': payment_methods, 'active_tab': 'payment_options'})


@login_required
@require_POST
def delete_payment_view(request, payment_id):
    """Delete payment method endpoint."""
    payment = get_object_or_404(PaymentOption, id=payment_id, user=request.user)
    payment.delete()
    messages.success(request, 'Payment method removed.')
    return redirect('mainsite:payment_options')


@login_required
def returns_view(request):
    """Order Returns Request View."""
    if request.method == 'POST':
        order_number = request.POST.get('order_number', '').strip()
        reason = request.POST.get('reason', '').strip()

        if not order_number or not reason:
            messages.error(request, 'Please provide both the order number and reason for return.')
            return redirect('mainsite:returns')

        order_exists = False
        if order_number.isdigit():
            order_exists = Order.objects.filter(id=int(order_number), user=request.user).exists()
        if not order_exists and hasattr(Order, 'order_number'):
            order_exists = Order.objects.filter(order_number=order_number, user=request.user).exists()

        if not order_exists:
            messages.error(request, 'No matching order found under your account.')
            return redirect('mainsite:returns')

        OrderReturn.objects.create(
            user=request.user,
            order_number=order_number,
            reason=reason
        )
        messages.success(request, 'Return request submitted successfully!')
        return redirect('mainsite:returns')

    returns = OrderReturn.objects.filter(user=request.user).order_by('-id')
    return render(request, 'mainsite/returns.html', {'returns': returns, 'active_tab': 'returns'})


@login_required
def cancellations_view(request):
    """Order Cancellations Request View."""
    if request.method == 'POST':
        order_number = request.POST.get('order_number', '').strip()
        reason = request.POST.get('reason', '').strip()

        if not order_number or not reason:
            messages.error(request, 'Please provide both the order number and reason for cancellation.')
            return redirect('mainsite:cancellations')

        order_exists = False
        if order_number.isdigit():
            order_exists = Order.objects.filter(id=int(order_number), user=request.user).exists()
        if not order_exists and hasattr(Order, 'order_number'):
            order_exists = Order.objects.filter(order_number=order_number, user=request.user).exists()

        if not order_exists:
            messages.error(request, 'No matching order found under your account.')
            return redirect('mainsite:cancellations')

        OrderCancellation.objects.create(
            user=request.user,
            order_number=order_number,
            reason=reason
        )
        messages.success(request, 'Cancellation request submitted successfully!')
        return redirect('mainsite:cancellations')

    cancellations = OrderCancellation.objects.filter(user=request.user).order_by('-id')
    return render(request, 'mainsite/cancellations.html', {'cancellations': cancellations, 'active_tab': 'cancellations'})


@login_required(login_url='account:login')
def dashboard_view(request):
    """A protected view accessible only by authenticated users."""
    context = {
        'user': request.user,
    }
    return render(request, 'mainsite/dashboard.html', context)


def custom_404_view(request, exception):
    """Custom 404 error handler view."""
    return render(request, 'mainsite/404.html', status=404)


def privacy_policy_view(request):
    return render(request, 'mainsite/privacy-policy.html')

def terms_of_use_view(request):
    return render(request, 'mainsite/terms-of-use.html')

def faq_view(request):
    return render(request, 'mainsite/faq.html')

