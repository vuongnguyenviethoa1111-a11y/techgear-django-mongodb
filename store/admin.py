from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'price', 'old_price', 'badge')
    list_filter = ('category',)
    search_fields = ('name', 'fabric', 'description')
