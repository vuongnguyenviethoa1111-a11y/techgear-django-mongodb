from django.contrib import admin
from .models import Category, Product, Order, OrderItem, Review

admin.site.site_header = "TECHGEAR LED & SMART DEVICES - QUẢN TRỊ HỆ THỐNG"
admin.site.site_title = "TechGear Admin"
admin.site.index_title = "Bảng điều khiển Danh mục, Thiết bị, Tồn kho, Bảo hành & Đơn hàng"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'brand', 'power_watt', 'connectivity', 'warranty_months', 'price', 'stock')
    list_filter = ('category', 'brand', 'warranty_months')
    search_fields = ('sku', 'name', 'brand', 'connectivity', 'specs_summary')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'payment_method', 'promo_code', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'phone', 'address')
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'reviewer_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer_name', 'comment', 'product__name')
