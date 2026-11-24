from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem, Review

admin.site.site_header = "TECHGEAR LED & SMART DEVICES - QUẢN TRỊ HỆ THỐNG"
admin.site.site_title = "TechGear Admin | Quản trị hệ thống"
admin.site.index_title = "Chọn Đơn hàng để thay đổi (Quản lý trạng thái đơn & Kích hoạt bảo hành điện tử)"


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
    list_display = (
        'id_badge',
        'full_name_bold',
        'phone_green',
        'payment_label',
        'promo_orange',
        'total_vnd',
        'status_pill',
        'created_at_fmt',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'phone', 'address')
    inlines = [OrderItemInline]

    @admin.display(description='ID', ordering='id')
    def id_badge(self, obj):
        return format_html('<strong style="color:#2563eb;">#{}</strong>', obj.id)

    @admin.display(description='HỌ TÊN NGƯỜI NHẬN', ordering='full_name')
    def full_name_bold(self, obj):
        return format_html('<strong style="color:#0f172a;">{}</strong>', obj.full_name)

    @admin.display(description='SĐT BẢO HÀNH', ordering='phone')
    def phone_green(self, obj):
        return format_html('<strong style="color:#0d9488;">{}</strong>', obj.phone)

    @admin.display(description='THANH TOÁN', ordering='payment_method')
    def payment_label(self, obj):
        return "Thanh toán COD" if obj.payment_method == 'cod' else "Chuyển khoản / QR Pay"

    @admin.display(description='MÃ KM', ordering='promo_code')
    def promo_orange(self, obj):
        code = obj.promo_code or "—"
        return format_html('<strong style="color:#ea580c;">{}</strong>', code)

    @admin.display(description='TỔNG TIỀN', ordering='total_price')
    def total_vnd(self, obj):
        formatted = f"{int(obj.total_price):,}".replace(",", ".")
        return format_html('<strong style="color:#0f172a;">{} VNĐ</strong>', formatted)

    @admin.display(description='TRẠNG THÁI ĐƠN', ordering='status')
    def status_pill(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<span style="background:#dbeafe; color:#1d4ed8; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem;">Chờ xác nhận</span>'
            )
        elif obj.status == 'completed':
            return format_html(
                '<span style="background:#ccfbf1; color:#0f766e; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem;">Đã hoàn thành (BH)</span>'
            )
        elif obj.status == 'shipping':
            return format_html(
                '<span style="background:#fef3c7; color:#b45309; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem;">Đang giao hàng</span>'
            )
        return format_html(
            '<span style="background:#ffe4e6; color:#e11d48; padding:4px 12px; border-radius:999px; font-weight:700; font-size:0.78rem;">Đã hủy</span>'
        )

    @admin.display(description='NGÀY ĐẶT', ordering='created_at')
    def created_at_fmt(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'reviewer_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer_name', 'comment', 'product__name')
