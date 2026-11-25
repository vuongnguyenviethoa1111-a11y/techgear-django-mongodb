from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Collection: categories - Phân loại danh mục thiết bị công nghệ & đèn LED."""
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Đường dẫn (slug)")

    class Meta:
        verbose_name = "Danh mục thiết bị"
        verbose_name_plural = "Danh mục thiết bị"

    def __str__(self):
        return self.name


class Product(models.Model):
    """Collection: products - Sản phẩm phụ kiện công nghệ, đèn LED & thiết bị thông minh."""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Danh mục")
    sku = models.CharField(max_length=40, default="TG-LED-01", verbose_name="Mã SKU kỹ thuật")
    name = models.CharField(max_length=200, verbose_name="Tên thiết bị / sản phẩm")
    brand = models.CharField(max_length=100, default="TechGear", verbose_name="Thương hiệu")
    price = models.PositiveIntegerField(verbose_name="Giá bán (VNĐ)")
    warranty_months = models.PositiveIntegerField(default=12, verbose_name="Bảo hành (tháng)")
    stock = models.PositiveIntegerField(default=20, verbose_name="Tồn kho")

    # Thông số kỹ thuật chi tiết
    power_watt = models.PositiveIntegerField(default=12, verbose_name="Công suất (W)")
    voltage = models.CharField(max_length=60, default="220V / USB-C 5V", verbose_name="Điện áp hoạt động")
    connectivity = models.CharField(max_length=100, default="Wi-Fi 2.4GHz / Bluetooth 5.3", verbose_name="Chuẩn kết nối")
    color_temp = models.CharField(max_length=100, default="RGB 16 triệu màu / 3000K-6500K", verbose_name="Nhiệt độ màu / Ánh sáng")
    lifespan_hours = models.PositiveIntegerField(default=30000, verbose_name="Tuổi thọ bóng/thiết bị (giờ)")
    variants = models.CharField(
        max_length=150,
        default="Bản Tiêu Chuẩn,Bản Pro Smart",
        verbose_name="Các phiên bản / Công suất tùy chọn (cách nhau dấu phẩy)"
    )
    specs_summary = models.CharField(max_length=255, default="Chip LED tiết kiệm điện, điều khiển qua App", verbose_name="Tóm tắt thông số kỹ thuật")
    image_url = models.TextField(blank=True, verbose_name="Link ảnh thiết bị (hoặc tải ảnh từ máy)")
    description = models.TextField(blank=True, verbose_name="Mô tả kỹ thuật chi tiết")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Thiết bị & Đèn LED"
        verbose_name_plural = "Thiết bị & Đèn LED"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.sku}] {self.name} ({self.price:,} VNĐ)"

    @property
    def variant_list(self):
        return [v.strip() for v in self.variants.split(',') if v.strip()]

    @property
    def display_image(self):
        if self.image_url:
            return self.image_url
        return "https://placehold.co/600x400/2563eb/ffffff?text=TechGear+Smart+LED"


class Order(models.Model):
    """Collection: orders - Đơn đặt hàng & thông tin kích hoạt bảo hành điện tử."""
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('shipping', 'Đang giao hàng'),
        ('completed', 'Đã hoàn thành (Đã kích hoạt bảo hành)'),
        ('cancelled', 'Đã hủy'),
    ]
    PAYMENT_CHOICES = [
        ('cod', 'Thanh toán khi nhận hàng (COD)'),
        ('banking', 'Chuyển khoản ngân hàng / QR Pay'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Tài khoản")
    full_name = models.CharField(max_length=150, verbose_name="Họ tên người nhận")
    phone = models.CharField(max_length=30, verbose_name="Số điện thoại (Tra cứu bảo hành)")
    address = models.TextField(verbose_name="Địa chỉ nhận hàng")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod', verbose_name="Phương thức thanh toán")
    promo_code = models.CharField(max_length=30, blank=True, verbose_name="Mã giảm giá")
    discount_amount = models.PositiveIntegerField(default=0, verbose_name="Số tiền giảm (VNĐ)")
    total_price = models.PositiveIntegerField(default=0, verbose_name="Tổng thanh toán (VNĐ)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái đơn")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đặt hàng")

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ['-created_at']

    def __str__(self):
        return f"Đơn #{self.id} - {self.full_name} ({self.total_price:,} VNĐ)"


class OrderItem(models.Model):
    """Collection: order_items - Chi tiết từng thiết bị và thời hạn bảo hành trong đơn."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Đơn hàng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Thiết bị")
    variant = models.CharField(max_length=80, default='Bản Tiêu Chuẩn', verbose_name="Phiên bản / Công suất")
    warranty_months = models.PositiveIntegerField(default=12, verbose_name="Bảo hành (tháng)")
    price = models.PositiveIntegerField(verbose_name="Đơn giá lúc mua (VNĐ)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")

    class Meta:
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Chi tiết đơn hàng"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} ({self.variant}) x {self.quantity}"


class Review(models.Model):
    """Collection: reviews - Đánh giá & nhận xét trải nghiệm kỹ thuật của khách hàng."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Thiết bị")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tài khoản")
    reviewer_name = models.CharField(max_length=100, default="Khách mua hàng", verbose_name="Tên người đánh giá")
    rating = models.PositiveIntegerField(default=5, verbose_name="Số sao (1-5)")
    comment = models.TextField(verbose_name="Nội dung nhận xét kỹ thuật")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đánh giá")

    class Meta:
        verbose_name = "Đánh giá thiết bị"
        verbose_name_plural = "Đánh giá thiết bị"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer_name} - {self.product.name} ({self.rating} sao)"


class CustomerAccount(User):
    """
    Proxy Model hiển thị mục 'Tài khoản người dùng' ngay trong khối
    QUẢN LÝ THIẾT BỊ CÔNG NGHỆ & ĐÈN LED (TECHGEAR) ở menu bên trái trang Admin.
    """
    class Meta:
        proxy = True
        verbose_name = "Tài khoản người dùng"
        verbose_name_plural = "Tài khoản người dùng"
