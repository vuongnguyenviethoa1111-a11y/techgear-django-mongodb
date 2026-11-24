"""
File: seed_data.py
Khởi tạo và đồng bộ dữ liệu khớp 100% với bộ ảnh Báo cáo đồ án TechGear:
- 4 Danh mục (`categories`)
- 8 Mã thiết bị (`products`) với Tổng tồn kho = 223 chiếc (sắp hết hàng: TG-SENS-PIR1 còn 8 chiếc)
- 2 Tài khoản (`users`): `admin` (admin@techgear.vn) và `vuongnguyenviethoa1111@gmail.com` / `sv.cntt@gmail.com`
- 2 Đơn hàng (`orders`) & 3 Chi tiết đơn (`order_items`):
  + Đơn #1: Nguyễn Văn A (Đơn mẫu BH) | 0901234567 | TECH20 | 279.200 VNĐ | Đã hoàn thành (BH)
  + Đơn #2: Vương Nguyễn Việt Hòa     | 0905123456 | TECH20 | 671.200 VNĐ | Chờ xác nhận
  => Tổng doanh thu = 950.400 VNĐ
- 8 Đánh giá kỹ thuật (`reviews`)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slimai_project.settings')
django.setup()

from django.contrib.auth.models import User
from shop.models import Category, Product, Order, OrderItem, Review
from shop.mongo_client import (
    INITIAL_CATEGORIES,
    INITIAL_PRODUCTS,
    MongoManager,
    sync_category_to_mongo,
    sync_product_to_mongo,
    sync_order_to_mongo,
    sync_review_to_mongo,
    sync_user_to_mongo,
)


def run_seed():
    MongoManager.ensure_collections()

    # 1. Tạo 2 Tài khoản chuẩn báo cáo (`users` = 2)
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@techgear.vn', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    student_user, s_created = User.objects.get_or_create(
        username='vuongnguyenviethoa1111@gmail.com',
        defaults={
            'email': 'vuongnguyenviethoa1111@gmail.com',
            'first_name': 'Vương Nguyễn Việt Hòa',
            'is_staff': False,
        }
    )
    if s_created:
        student_user.set_password('Hoa2026cnpm')
        student_user.save()

    for u in User.objects.all():
        sync_user_to_mongo(u)

    # 2. Đồng bộ 4 Danh mục (`categories` = 4)
    cat_map = {}
    for c in INITIAL_CATEGORIES:
        cat, _ = Category.objects.update_or_create(
            slug=c['slug'],
            defaults={'name': c['name']}
        )
        cat_map[c['slug']] = cat
        sync_category_to_mongo(cat)

    # 3. Đồng bộ 8 Sản phẩm (`products` = 8, tổng tồn kho = 223 chiếc)
    prod_by_sku = {}
    for item in INITIAL_PRODUCTS:
        prod, _ = Product.objects.update_or_create(
            sku=item['sku'],
            defaults={
                'category': cat_map[item['category_slug']],
                'name': item['name'],
                'brand': item['brand'],
                'price': item['price'],
                'warranty_months': item['warranty_months'],
                'stock': item['stock'],
                'power_watt': item['power_watt'],
                'voltage': item['voltage'],
                'connectivity': item['connectivity'],
                'color_temp': item['color_temp'],
                'lifespan_hours': item['lifespan_hours'],
                'variants': item['variants'],
                'specs_summary': item['specs_summary'],
                'description': item['description'],
                'image_url': item['image_url'],
            }
        )
        prod_by_sku[item['sku']] = prod
        sync_product_to_mongo(prod)

        # 4. Đồng bộ 8 Đánh giá kỹ thuật (`reviews` = 8)
        rev, _ = Review.objects.update_or_create(
            product=prod,
            reviewer_name='sv.cntt@gmail.com',
            defaults={
                'user': student_user,
                'rating': 5,
                'comment': f"Thiết bị {prod.name} hoạt động ổn định, đúng công suất {prod.power_watt}W, kết nối {prod.connectivity} rất nhạy.",
            }
        )
        sync_review_to_mongo(rev)

    # 5. Tạo đúng 2 Đơn hàng mẫu (`orders` = 2) và 3 Chi tiết đơn (`order_items` = 3)
    # để Tổng doanh thu đúng 950.400 VNĐ (279.200 + 671.200) y hệt ảnh chụp báo cáo
    p_led = prod_by_sku.get('TG-LED-RGB05')   # 349.000 VNĐ
    p_bar = prod_by_sku.get('TG-BAR-PC01')    # 490.000 VNĐ

    if p_led and p_bar and Order.objects.count() < 2:
        Order.objects.all().delete()

        # Đơn #1: Nguyễn Văn A (Đơn mẫu BH) - 1 x 349.000 (-20% TECH20) = 279.200 VNĐ
        order1 = Order.objects.create(
            id=1,
            user=admin_user,
            full_name='Nguyễn Văn A (Đơn mẫu BH)',
            phone='0901234567',
            address='Khu Công Nghệ Cao, TP. Thủ Đức, TP.HCM',
            payment_method='cod',
            promo_code='TECH20',
            discount_amount=69800,
            total_price=279200,
            status='completed',
        )
        oi1 = OrderItem.objects.create(
            order=order1,
            product=p_led,
            variant='Cuộn 5m (24W)',
            warranty_months=p_led.warranty_months,
            price=p_led.price,
            quantity=1,
        )
        sync_order_to_mongo(order1, [oi1], decrement_mongo_stock=False)

        # Đơn #2: Vương Nguyễn Việt Hòa - (349.000 + 490.000 = 839.000, -20% TECH20 = 671.200 VNĐ)
        order2 = Order.objects.create(
            id=2,
            user=student_user,
            full_name='Vương Nguyễn Việt Hòa',
            phone='0905123456',
            address='Đại học Công Nghệ Thông Tin, TP.HCM',
            payment_method='cod',
            promo_code='TECH20',
            discount_amount=167800,
            total_price=671200,
            status='pending',
        )
        oi2 = OrderItem.objects.create(
            order=order2,
            product=p_led,
            variant='Cuộn 5m (24W)',
            warranty_months=p_led.warranty_months,
            price=p_led.price,
            quantity=1,
        )
        oi3 = OrderItem.objects.create(
            order=order2,
            product=p_bar,
            variant='Bản Cảm Ứng',
            warranty_months=p_bar.warranty_months,
            price=p_bar.price,
            quantity=1,
        )
        sync_order_to_mongo(order2, [oi2, oi3], decrement_mongo_stock=False)
    else:
        for ord_obj in Order.objects.prefetch_related('items__product').all():
            sync_order_to_mongo(ord_obj, list(ord_obj.items.all()), decrement_mongo_stock=False)

    info = MongoManager.status_info()
    print("=================================================================")
    print(f"-> Database MongoDB Atlas: {info['db_name']} | Connected: {info['connected']}")
    print(f"-> Số lượng documents trong 6 collections: {info['counts']}")
    print("=================================================================")


if __name__ == '__main__':
    run_seed()
