from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Tên danh mục')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Đường dẫn (slug)')),
            ],
            options={
                'verbose_name': 'Danh mục thiết bị',
                'verbose_name_plural': 'Danh mục thiết bị',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='Họ tên người nhận')),
                ('phone', models.CharField(max_length=30, verbose_name='Số điện thoại (Tra cứu bảo hành)')),
                ('address', models.TextField(verbose_name='Địa chỉ nhận hàng')),
                ('payment_method', models.CharField(choices=[('cod', 'Thanh toán khi nhận hàng (COD)'), ('banking', 'Chuyển khoản ngân hàng / QR Pay')], default='cod', max_length=20, verbose_name='Phương thức thanh toán')),
                ('promo_code', models.CharField(blank=True, max_length=30, verbose_name='Mã giảm giá')),
                ('discount_amount', models.PositiveIntegerField(default=0, verbose_name='Số tiền giảm (VNĐ)')),
                ('total_price', models.PositiveIntegerField(default=0, verbose_name='Tổng thanh toán (VNĐ)')),
                ('status', models.CharField(choices=[('pending', 'Chờ xác nhận'), ('shipping', 'Đang giao hàng'), ('completed', 'Đã hoàn thành (Đã kích hoạt bảo hành)'), ('cancelled', 'Đã hủy')], default='pending', max_length=20, verbose_name='Trạng thái đơn')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ngày đặt hàng')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Tài khoản')),
            ],
            options={
                'verbose_name': 'Đơn hàng',
                'verbose_name_plural': 'Đơn hàng',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(default='TG-LED-01', max_length=40, verbose_name='Mã SKU kỹ thuật')),
                ('name', models.CharField(max_length=200, verbose_name='Tên thiết bị / sản phẩm')),
                ('brand', models.CharField(default='TechGear', max_length=100, verbose_name='Thương hiệu')),
                ('price', models.PositiveIntegerField(verbose_name='Giá bán (VNĐ)')),
                ('warranty_months', models.PositiveIntegerField(default=12, verbose_name='Bảo hành (tháng)')),
                ('stock', models.PositiveIntegerField(default=20, verbose_name='Tồn kho')),
                ('power_watt', models.PositiveIntegerField(default=12, verbose_name='Công suất (W)')),
                ('voltage', models.CharField(default='220V / USB-C 5V', max_length=60, verbose_name='Điện áp hoạt động')),
                ('connectivity', models.CharField(default='Wi-Fi 2.4GHz / Bluetooth 5.3', max_length=100, verbose_name='Chuẩn kết nối')),
                ('color_temp', models.CharField(default='RGB 16 triệu màu / 3000K-6500K', max_length=100, verbose_name='Nhiệt độ màu / Ánh sáng')),
                ('lifespan_hours', models.PositiveIntegerField(default=30000, verbose_name='Tuổi thọ bóng/thiết bị (giờ)')),
                ('variants', models.CharField(default='Bản Tiêu Chuẩn,Bản Pro Smart', max_length=150, verbose_name='Các phiên bản / Công suất tùy chọn (cách nhau dấu phẩy)')),
                ('specs_summary', models.CharField(default='Chip LED tiết kiệm điện, điều khiển qua App', max_length=255, verbose_name='Tóm tắt thông số kỹ thuật')),
                ('image_url', models.URLField(blank=True, max_length=500, verbose_name='Link ảnh thiết bị')),
                ('description', models.TextField(blank=True, verbose_name='Mô tả kỹ thuật chi tiết')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='shop.category', verbose_name='Danh mục')),
            ],
            options={
                'verbose_name': 'Thiết bị & Đèn LED',
                'verbose_name_plural': 'Thiết bị & Đèn LED',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant', models.CharField(default='Bản Tiêu Chuẩn', max_length=80, verbose_name='Phiên bản / Công suất')),
                ('warranty_months', models.PositiveIntegerField(default=12, verbose_name='Bảo hành (tháng)')),
                ('price', models.PositiveIntegerField(verbose_name='Đơn giá lúc mua (VNĐ)')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Số lượng')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='shop.order', verbose_name='Đơn hàng')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.product', verbose_name='Thiết bị')),
            ],
            options={
                'verbose_name': 'Chi tiết đơn hàng',
                'verbose_name_plural': 'Chi tiết đơn hàng',
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reviewer_name', models.CharField(default='Khách mua hàng', max_length=100, verbose_name='Tên người đánh giá')),
                ('rating', models.PositiveIntegerField(default=5, verbose_name='Số sao (1-5)')),
                ('comment', models.TextField(verbose_name='Nội dung nhận xét kỹ thuật')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ngày đánh giá')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='shop.product', verbose_name='Thiết bị')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Tài khoản')),
            ],
            options={
                'verbose_name': 'Đánh giá thiết bị',
                'verbose_name_plural': 'Đánh giá thiết bị',
                'ordering': ['-created_at'],
            },
        ),
    ]
