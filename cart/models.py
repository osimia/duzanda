# duzanda/cart/models.py

from django.db import models
from accounts.models import User
from products.models import Product

class CartItem(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        size_str = f" [{self.size}]" if self.size else ""
        return f"{self.product.name}{size_str} x {self.quantity} for {self.buyer.username}"
