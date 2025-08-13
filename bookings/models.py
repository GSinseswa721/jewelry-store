# bookings/models.py
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class JewelryCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., "Rings", "Necklaces", "Bracelets", "Earrings"
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Jewelry Categories"
    
    def __str__(self):
        return self.name


class JewelryItem(models.Model):
    ITEM_CHOICES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('pearls', 'Pearls'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(JewelryCategory, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jewelry_items')
    description = models.TextField()
    item_type = models.CharField(max_length=20, choices=ITEM_CHOICES, default='gold')
    weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Weight in grams")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='jewelry_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.item_type}"


class BuyCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.user.username}"


class JewelryPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    buy_code = models.ForeignKey(BuyCode, on_delete=models.CASCADE)
    jewelry_item = models.ForeignKey(JewelryItem, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jewelry_purchases')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate total cost
        self.total_cost = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Purchase: {self.jewelry_item.name} by {self.buyer.username}"


class PurchaseReview(models.Model):
    purchase = models.OneToOneField(JewelryPurchase, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.purchase.jewelry_item.name} - {self.rating} stars"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('purchase', 'Purchase Payment'),
        ('refund', 'Refund'),
    ]
    
    purchase = models.ForeignKey(JewelryPurchase, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount}"


# View functions
def purchase_confirmation(request, purchase_id):
    purchase = get_object_or_404(JewelryPurchase, id=purchase_id)
    return render(request, 'confirmation.html', {'purchase': purchase})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('index')  # Redirect to homepage or another page
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})