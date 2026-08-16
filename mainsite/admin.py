from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    Coupon,
    Profile,
    Address,
    PaymentOption,
    OrderReturn,
    OrderCancellation,
    Cart,
    CartItem,
    Order,
    OrderItem,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug',]
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'discount_price', 'stock',
        'is_active', 'is_featured', 'flashsales', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_featured', 'flashsales', 
        'best_selling_products', 'explore_our_products', 'category'
    ]
    list_editable = ['price', 'discount_price', 'stock', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['category']
    inlines = [ProductImageInline]

    fieldsets = (
        ('General Info', {
            'fields': ('name', 'slug', 'category', 'image', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('Badges & Ratings', {
            'fields': ('badge', 'rating', 'review_count')
        }),
        ('Visibility & Display Filters', {
            'fields': (
                'is_active', 'is_featured', 'flashsales',
                'best_selling_products', 'explore_our_products'
            )
        }),
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'active', 'valid_from', 'valid_to', 'is_valid_coupon']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']

    @admin.display(boolean=True, description='Currently Valid')
    def is_valid_coupon(self, obj):
        return obj.is_valid()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address']
    search_fields = ['user__username', 'user__email', 'phone']
    raw_id_fields = ['user']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'street_address', 'city', 'state', 'country', 'is_default']
    list_filter = ['is_default', 'country']
    search_fields = ['full_name', 'street_address', 'city', 'user__username', 'user__email']
    raw_id_fields = ['user']


@admin.register(PaymentOption)
class PaymentOptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'card_holder_name', 'card_type', 'last_four', 'is_default']
    list_filter = ['card_type', 'is_default']
    search_fields = ['card_holder_name', 'last_four', 'user__username', 'user__email']
    raw_id_fields = ['user']


@admin.register(OrderReturn)
class OrderReturnAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'user__username', 'user__email', 'reason']
    raw_id_fields = ['user', 'order']


@admin.register(OrderCancellation)
class OrderCancellationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'user__username', 'user__email', 'reason']
    raw_id_fields = ['user', 'order']


class CartItemInline(admin.TabularInline):
    model = CartItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'get_subtotal', 'created_at', 'updated_at']
    search_fields = ['user__username', 'session_id']
    raw_id_fields = ['user']
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_cost']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'get_customer_name', 'email', 'payment_method',
        'total_amount', 'status', 'is_paid', 'created_at'
    ]
    list_filter = ['status', 'is_paid', 'payment_method', 'created_at']
    list_editable = ['status', 'is_paid']
    search_fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'street_address']
    raw_id_fields = ['user']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at']
    actions = ['mark_as_paid', 'mark_as_processing', 'mark_as_shipped']

    fieldsets = (
        ('Customer Info', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone', 'company_name')
        }),
        ('Shipping Address', {
            'fields': ('street_address', 'apartment', 'city')
        }),
        ('Payment & Totals', {
            'fields': ('payment_method', 'subtotal', 'shipping_cost', 'discount_amount', 'total_amount', 'is_paid')
        }),
        ('Order Status', {
            'fields': ('status', 'created_at')
        }),
    )

    @admin.display(description='Customer Name')
    def get_customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    # Bulk Action Helpers
    @admin.action(description="Mark selected orders as Paid")
    def mark_as_paid(self, request, queryset):
        queryset.update(is_paid=True)

    @admin.action(description="Mark selected orders as Processing")
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')

    @admin.action(description="Mark selected orders as Shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')