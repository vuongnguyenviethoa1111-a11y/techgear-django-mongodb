from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Áo thun', 'Áo thun'),
        ('Sơ mi', 'Sơ mi'),
        ('Quần âu', 'Quần âu'),
        ('Đồ thể thao', 'Đồ thể thao'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.PositiveIntegerField(help_text="Giá bán (VNĐ)")
    old_price = models.PositiveIntegerField(default=0, help_text="Giá gốc (VNĐ)")
    badge = models.CharField(max_length=80, blank=True)
    emoji = models.CharField(max_length=16, default='👕')
    fabric = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.price:,} ₫)"
