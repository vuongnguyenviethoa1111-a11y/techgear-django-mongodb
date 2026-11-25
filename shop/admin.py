from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product, Order, OrderItem, Review, CustomerAccount

admin.site.site_header = "TECHGEAR LED & SMART DEVICES - QUẢN TRỊ HỆ THỐNG"
admin.site.site_title = "TechGear Admin | Quản trị hệ thống"
admin.site.index_title = "Bảng điều khiển Quản lý Thiết bị, Đơn hàng, Bảo hành & Tài khoản người dùng"


class ImageUrlOrUploadWidget(forms.TextInput):
    """
    Widget cho phép Admin:
    1. Dán trực tiếp Link ảnh (URL) từ Internet.
    2. Hoặc bấm nút '📁 Chọn ảnh từ máy tính' -> tự động đọc file sang DataURL (Base64)
       và hiển thị ảnh xem trước ngay lập tức (không bao giờ mất ảnh khi deploy trên Railway).
    """
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['style'] = 'width: 75%; max-width: 520px; padding: 7px 10px;'
        attrs['placeholder'] = 'Dán link ảnh (https://...) hoặc bấm nút Chọn ảnh từ máy bên dưới...'
        input_html = super().render(name, value, attrs, renderer)
        input_id = attrs.get('id', f'id_{name}')
        preview_src = value if value else 'https://placehold.co/600x400/2563eb/ffffff?text=Preview'

        extra_ui = f"""
        <div style="margin-top: 10px; display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
            <label for="{input_id}_file_picker" style="
                display: inline-flex; align-items: center; gap: 6px;
                background: #2563eb; color: #ffffff; padding: 7px 14px;
                border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;
            ">
                📁 Chọn ảnh từ máy tính
            </label>
            <input type="file" id="{input_id}_file_picker" accept="image/*" style="display:none;" />
            <button type="button" id="{input_id}_url_btn" style="
                background: #0d9488; color: #ffffff; border: none; padding: 7px 14px;
                border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;
            ">
                🔗 Nhập Link ảnh (URL)
            </button>
            <span id="{input_id}_status" style="font-size: 12px; color: #0d9488; font-weight: 600;"></span>
        </div>
        <div style="margin-top: 10px;">
            <img id="{input_id}_preview" src="{preview_src}" alt="Xem trước ảnh" style="
                max-height: 130px; max-width: 240px; border-radius: 8px;
                border: 1px solid #cbd5e1; object-fit: cover; display: {'block' if value else 'none'};
            " />
        </div>
        <script>
        (function() {{
            var textInput = document.getElementById('{input_id}');
            var fileInput = document.getElementById('{input_id}_file_picker');
            var urlBtn = document.getElementById('{input_id}_url_btn');
            var preview = document.getElementById('{input_id}_preview');
            var status = document.getElementById('{input_id}_status');
            if (!textInput || !fileInput) return;

            textInput.addEventListener('input', function() {{
                if (textInput.value.trim()) {{
                    preview.src = textInput.value.trim();
                    preview.style.display = 'block';
                }}
            }});

            urlBtn.addEventListener('click', function() {{
                var current = textInput.value.startsWith('http') ? textInput.value : '';
                var entered = prompt('Dán đường dẫn (URL) ảnh thiết bị vào đây:', current);
                if (entered !== null && entered.trim() !== '') {{
                    textInput.value = entered.trim();
                    preview.src = entered.trim();
                    preview.style.display = 'block';
                    status.textContent = '✓ Đã gắn link ảnh từ URL!';
                }}
            }});

            fileInput.addEventListener('change', function(e) {{
                var file = e.target.files && e.target.files[0];
                if (!file) return;
                var reader = new FileReader();
                reader.onload = function(evt) {{
                    textInput.value = evt.target.result;
                    preview.src = evt.target.result;
                    preview.style.display = 'block';
                    status.textContent = '✓ Đã tải ảnh "' + file.name + '" từ máy tính!';
                }};
                reader.readAsDataURL(file);
            }});
        }})();
        </script>
        """
        return mark_safe(input_html + extra_ui)


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'image_url': ImageUrlOrUploadWidget(),
        }


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
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


@admin.register(CustomerAccount)
class CustomerAccountAdmin(UserAdmin):
    """
    Quản lý 'Tài khoản người dùng' trực tiếp trong mục
    QUẢN LÝ THIẾT BỊ CÔNG NGHỆ & ĐÈN LED (TECHGEAR) ở menu bên trái Admin.
    """
    list_display = ('username', 'email', 'first_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name')
