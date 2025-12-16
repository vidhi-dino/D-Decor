from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['get_total_price']
    fields = ['product_name', 'product_price', 'quantity', 'get_total_price']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_items', 'get_formatted_total_price', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'get_total_items', 'get_formatted_total_price']
    inlines = [CartItemInline]
    
    def get_formatted_total_price(self, obj):
        return f"₹{obj.get_total_price():.2f}"
    get_formatted_total_price.short_description = 'Total Price'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'get_user', 'quantity', 'product_price', 'get_formatted_total_price', 'added_at']
    list_filter = ['added_at', 'cart__user']
    search_fields = ['product_name', 'cart__user__username']
    readonly_fields = ['added_at', 'updated_at', 'get_total_price']
    
    def get_user(self, obj):
        return obj.cart.user.username
    get_user.short_description = 'User'
    
    def get_formatted_total_price(self, obj):
        return f"₹{obj.get_total_price():.2f}"
    get_formatted_total_price.short_description = 'Total'