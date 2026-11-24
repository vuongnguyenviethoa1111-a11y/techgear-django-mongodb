"""
File: seed_data.py
Đẩy toàn bộ dữ liệu hàng hóa hiện có trong code/web lên MongoDB Atlas (`techgear_db`)
cho đủ 6 collections:
- `categories`
- `products`
- `orders`
- `order_items`
- `reviews`
- `users`
Sử dụng cơ chế Upsert (khớp theo `slug`, `sku` hoặc `name`) để cập nhật giá, tồn kho,
mô tả, thông số kỹ thuật thay vì tạo bản ghi trùng lặp.
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

    # 1. Đồng bộ Người dùng (`users`)
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@techgear.vn', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("-> Đã tạo tài khoản quản trị: user='admin' / pass='admin123'")

    for u in User.objects.all():
        sync_user_to_mongo(u)

    # 2. Đồng bộ Danh mục (`categories`) - Khớp theo `slug` hoặc `name`
    cat_map = {}
    for c in INITIAL_CATEGORIES:
        cat, _ = Category.objects.update_or_create(
            slug=c['slug'],
            defaults={'name': c['name']}
        )
        cat_map[c['slug']] = cat
        sync_category_to_mongo(cat)

    # 3. Đồng bộ Sản phẩm (`products`) - Khớp theo `sku` hoặc `name`
    first_product = None
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
        if first_product is None:
            first_product = prod
        sync_product_to_mongo(prod)

        # 4. Đồng bộ Đánh giá (`reviews`)
        rev, _ = Review.objects.update_or_create(
            product=prod,
            reviewer_name='sv.cntt@gmail.com',
            defaults={
                'user': admin_user,
                'rating': 5,
                'comment': f"Thiết bị {prod.name} hoạt động ổn định, đúng công suất {prod.power_watt}W, kết nối {prod.connectivity} rất nhạy.",
            }
        )
        sync_review_to_mongo(rev)

    # 5. Đồng bộ Đơn hàng & Chi tiết đơn (`orders`, `order_items`)
    if first_product and not Order.objects.exists():
        sample_order = Order.objects.create(
            user=admin_user,
            full_name='Nguyễn Văn A (Đơn mẫu Bảo hành)',
            phone='0901234567',
            address='Khu Công Nghệ Cao, TP. Thủ Đức, TP.HCM',
            payment_method='cod',
            promo_code='TECH20',
            discount_amount=int(first_product.price * 0.2),
            total_price=int(first_product.price * 0.8),
            status='completed',
        )
        sample_item = OrderItem.objects.create(
            order=sample_order,
            product=first_product,
            variant=first_product.variant_list[0],
            warranty_months=first_product.warranty_months,
            price=first_product.price,
            quantity=1,
        )
        sync_order_to_mongo(sample_order, [sample_item], decrement_mongo_stock=False)
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
