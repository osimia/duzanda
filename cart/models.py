# duzanda/cart/models.py

from django.db import models
from accounts.models import User
from products.models import Product

class CartItem(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} for {self.buyer.username}"
