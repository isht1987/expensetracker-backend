from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Fuel Expenses', 'Fuel Expenses'),
        ('Meals', 'Meals'),
        ('Car Payments', 'Car Payments'),
        ('Insurance', 'Insurance'),
        ('Car Maintenance', 'Car Maintenance'),
        ('Car Repair', 'Car Repair'),
        ('Legal Fines', 'Legal Fines'),
        ('Others', 'Others'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    receipt_image = models.ImageField(upload_to='receipts/%Y/%m/%d/', null=True, blank=True)
    date = models.DateField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    custom_category = models.CharField(max_length=100, blank=True, help_text="Required when category is 'Others'")
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['category']),
        ]
    
    def get_category_display_name(self):
        """Returns the custom category if 'Others' is selected, otherwise returns the category"""
        if self.category == 'Others' and self.custom_category:
            return self.custom_category
        return self.category
    
    def __str__(self):
        return f"{self.user.username} - {self.get_category_display_name()} - ${self.amount} - {self.date}"