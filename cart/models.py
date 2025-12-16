from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s cart"
    
    def get_total_items(self):
        """Calculate total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    def get_total_price(self):
        """Calculate total price of all items in cart"""
        return sum(item.get_total_price() for item in self.items.all())
    
    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.URLField(max_length=500, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-added_at']
        unique_together = ['cart', 'product_name']
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
    
    def get_total_price(self):
        """Calculate total price for this item (price × quantity)"""
        return self.product_price * self.quantity