"""
File: shop/mongo_client.py
Tầng thao tác Đọc / Ghi / Cập nhật (Upsert) trực tiếp vào MongoDB Atlas (`techgear_db`)
sử dụng kết nối từ `mongo_db.py` trên đúng 6 collections:
1. `categories`
2. `products`
3. `orders`
4. `order_items`
5. `reviews`
6. `users`
"""
from datetime import datetime
from mongo_db import (
    MONGO_URI,
    MONGO_DB_NAME,
    PYMONGO_AVAILABLE,
    ASCENDING,
    DESCENDING,
    db,
    check_mongo_connection,
    categories_col,
    products_col,
    orders_col,
    order_items_col,
    reviews_col,
    users_col,
)

REQUIRED_COLLECTIONS = [
    "categories",
    "products",
    "orders",
    "order_items",
    "reviews",
    "users",
]

# ==============================================================================
# DỮ LIỆU HÀNG HÓA CHUẨN TRONG CODE/WEB ĐỂ ĐẨY LÊN `categories` & `products`
# ==============================================================================
INITIAL_CATEGORIES = [
    {"name": "Đèn LED Thông Minh", "slug": "den-led-thong-minh"},
    {"name": "Thiết Bị Smart Home", "slug": "thiet-bi-smart-home"},
    {"name": "Đèn Bàn & Góc Setup PC", "slug": "den-ban-setup-pc"},
    {"name": "Phụ Kiện Công Nghệ IT", "slug": "phu-kien-cong-nghe"},
]

INITIAL_PRODUCTS = [
    {
        "category_slug": "den-led-thong-minh",
        "sku": "TG-LED-RGB05",
        "slug": "cuon-day-den-led-rgbic-5m-dong-bo-nhac-wifi",
        "name": "Cuộn Dây Đèn LED RGBIC 5m Đồng Bộ Nhạc Wi-Fi",
        "brand": "TechGear Light",
        "price": 349000,
        "warranty_months": 18,
        "stock": 35,
        "power_watt": 24,
        "voltage": "Adapter DC 12V / 2A",
        "connectivity": "Wi-Fi 2.4GHz + Bluetooth 5.2 (App & Giọng nói)",
        "color_temp": "RGBIC 16 triệu màu + Nháy theo nhạc Mic tích hợp",
        "lifespan_hours": 35000,
        "variants": "Cuộn 5m (24W),Cuộn 10m Pro (36W)",
        "specs_summary": "Chip LED 5050 phủ keo chống ẩm IP65, điều khiển qua App điện thoại.",
        "description": "Cuộn dây đèn LED RGBIC 5m tích hợp vi điều khiển độc lập từng đoạn màu, đồng bộ nhịp nhạc qua micro độ nhạy cao và điều khiển từ xa qua Wi-Fi 2.4GHz.",
        "image_url": "https://placehold.co/600x400/2563eb/ffffff?text=Day+LED+RGBIC+5m",
    },
    {
        "category_slug": "den-led-thong-minh",
        "sku": "TG-BULB-W12",
        "slug": "bong-den-led-smart-bulb-e27-doi-mau-wifi-12w",
        "name": "Bóng Đèn LED Smart Bulb E27 Đổi Màu Wi-Fi 12W",
        "brand": "LumiSmart",
        "price": 189000,
        "warranty_months": 24,
        "stock": 50,
        "power_watt": 12,
        "voltage": "AC 220V - 50Hz (Đui xoáy E27)",
        "connectivity": "Wi-Fi 2.4GHz (Hỗ trợ Google Home / Alexa)",
        "color_temp": "RGB + Trắng Ấm đến Trắng Lạnh (2700K - 6500K)",
        "lifespan_hours": 40000,
        "variants": "Bóng 9W,Bóng 12W Siêu Sáng",
        "specs_summary": "Quang thông 1100 Lumens, hẹn giờ bật tắt tự động không cần Hub.",
        "description": "Bóng đèn LED thông minh chuẩn đui E27 thông dụng, cho phép tùy chỉnh độ sáng 1%-100%, đổi 16 triệu màu RGB và hẹn giờ tự động qua smartphone.",
        "image_url": "https://placehold.co/600x400/0d9488/ffffff?text=Smart+LED+Bulb+12W",
    },
    {
        "category_slug": "den-ban-setup-pc",
        "sku": "TG-BAR-PC01",
        "slug": "thanh-den-led-treo-man-hinh-pc-chong-can-asymmetric",
        "name": "Thanh Đèn LED Treo Màn Hình PC Chống Cận Asymmetric",
        "brand": "TechGear Desk",
        "price": 490000,
        "warranty_months": 18,
        "stock": 22,
        "power_watt": 10,
        "voltage": "USB Type-C 5V / 2A",
        "connectivity": "Núm xoay không dây 2.4GHz / Cảm ứng chạm",
        "color_temp": "3 chế độ màu: 2900K - 4200K - 6500K (CRI Ra > 95)",
        "lifespan_hours": 30000,
        "variants": "Bản Cảm Ứng,Bản Kèm Núm Xoay Không Dây",
        "specs_summary": "Góc chiếu bất đối xứng không gây lóa màn hình, chỉ số hoàn màu CRI > 95.",
        "description": "Thanh đèn LED kẹp trực tiếp lên cạnh trên màn hình máy tính, thiết kế quang học bất đối xứng chỉ chiếu sáng bàn phím và tài liệu, bảo vệ mắt ban đêm.",
        "image_url": "https://placehold.co/600x400/ff5a36/ffffff?text=Den+Treo+Man+Hinh+PC",
    },
    {
        "category_slug": "den-ban-setup-pc",
        "sku": "TG-AMB-BAR2",
        "slug": "cap-den-led-ambiance-dat-ban-dong-bo-man-hinh-pc",
        "name": "Cặp Đèn LED Ambiance Đặt Bàn Đồng Bộ Màn Hình PC",
        "brand": "TechGear Light",
        "price": 560000,
        "warranty_months": 12,
        "stock": 16,
        "power_watt": 15,
        "voltage": "USB-C 5V / Adapter 12V",
        "connectivity": "USB-C Sync PC + Bluetooth App",
        "color_temp": "RGBIC Ambilight theo màu màn hình",
        "lifespan_hours": 30000,
        "variants": "Bộ 2 Thanh Đứng,Bộ 2 Thanh + Hub Sync PC",
        "specs_summary": "Đồng bộ màu sắc thời gian thực theo game và phim trên máy tính.",
        "description": "Bộ 2 thanh đèn LED RGBIC đặt hai bên màn hình PC, tự động đọc màu sắc khung hình game/phim qua cổng USB-C để tạo hiệu ứng ánh sáng tràn viền.",
        "image_url": "https://placehold.co/600x400/8b5cf6/ffffff?text=LED+Ambiance+Setup+PC",
    },
    {
        "category_slug": "thiet-bi-smart-home",
        "sku": "TG-PLUG-W20",
        "slug": "o-cam-thong-minh-wifi-do-cong-suat-tieu-thu-dien-20a",
        "name": "Ổ Cắm Thông Minh Wi-Fi Đo Công Suất Tiêu Thụ Điện 20A",
        "brand": "SmartLife Tech",
        "price": 210000,
        "warranty_months": 12,
        "stock": 45,
        "power_watt": 4400,
        "voltage": "AC 100-240V ~ Max 20A",
        "connectivity": "Wi-Fi 2.4GHz + Bluetooth Pairing",
        "color_temp": "Đèn báo trạng thái LED xanh dịu",
        "lifespan_hours": 50000,
        "variants": "Bản 16A Tiêu Chuẩn,Bản 20A Có Đo Điện Năng",
        "specs_summary": "Theo dõi số kWh điện tiêu thụ trên điện thoại, hẹn giờ tắt sạc an toàn.",
        "description": "Ổ cắm thông minh chịu tải cao 20A (4400W), tích hợp chip đo công suất thực tế (W, V, A, kWh) theo ngày/tháng và tự ngắt khi quá tải.",
        "image_url": "https://placehold.co/600x400/0284c7/ffffff?text=O+Cam+WiFi+Smart+20A",
    },
    {
        "category_slug": "thiet-bi-smart-home",
        "sku": "TG-SENS-PIR1",
        "slug": "den-led-cam-bien-chuyen-dong-hong-ngoai-pir-pin-sac-type-c",
        "name": "Đèn LED Cảm Biến Chuyển Động Hồng Ngoại PIR Pin Sạc Type-C",
        "brand": "LumiSmart",
        "price": 165000,
        "warranty_months": 12,
        "stock": 8,
        "power_watt": 5,
        "voltage": "Pin Lithium 2000mAh (Sạc USB-C 5V)",
        "connectivity": "Cảm biến chuyển động PIR 120° + Cảm biến ánh sáng",
        "color_temp": "Trắng ấm 3000K / Trắng tự nhiên 4500K",
        "lifespan_hours": 25000,
        "variants": "Thanh 30cm,Thanh 50cm Pin Lớn",
        "specs_summary": "Tự bật sáng khi có người đi qua trong tối, gắn nam châm cầu thang/tủ áo.",
        "description": "Thanh đèn LED không dây tích hợp cảm biến thân nhiệt hồng ngoại PIR góc rộng 120 độ, chỉ bật khi trời tối và tự tắt sau 20 giây không có chuyển động.",
        "image_url": "https://placehold.co/600x400/f59e0b/ffffff?text=Den+Cam+Bien+PIR",
    },
    {
        "category_slug": "phu-kien-cong-nghe",
        "sku": "TG-GAN-65W",
        "slug": "cu-sac-nhanh-gan-65w-3-cong-co-led-bao-cong-suat",
        "name": "Củ Sạc Nhanh GaN 65W 3 Cổng (2 USB-C + 1 USB-A) Có LED Báo Công Suất",
        "brand": "TechGear Power",
        "price": 440000,
        "warranty_months": 24,
        "stock": 28,
        "power_watt": 65,
        "voltage": "Input 100-240V / Output PD 20V-3.25A",
        "connectivity": "USB-C Power Delivery 3.0 / PPS / QC 4.0",
        "color_temp": "Màn hình LED kỹ thuật số hiển thị số Watt",
        "lifespan_hours": 45000,
        "variants": "Bản 65W GaN,Bản 65W Kèm Cáp C-to-C 100W",
        "specs_summary": "Chip bán dẫn GaN mát hơn 30%, sạc được cả Laptop, MacBook và Điện thoại.",
        "description": "Củ sạc công nghệ Gallium Nitride (GaN) thế hệ mới công suất 65W, trang bị màn hình LED hiển thị trực tiếp số Watt đang sạc theo thời gian thực.",
        "image_url": "https://placehold.co/600x400/1e40af/ffffff?text=Sac+GaN+65W+LED+Watt",
    },
    {
        "category_slug": "phu-kien-cong-nghe",
        "sku": "TG-HUB-8IN1",
        "slug": "hub-chuyen-doi-type-c-8-in-1-hdmi-4k-lan-gigabit-pd-100w",
        "name": "Hub Chuyển Đổi Type-C 8-in-1 (HDMI 4K, LAN Gigabit, PD 100W)",
        "brand": "TechGear Pro",
        "price": 520000,
        "warranty_months": 18,
        "stock": 19,
        "power_watt": 100,
        "voltage": "USB-C Bus Powered + PD Pass-through 100W",
        "connectivity": "USB-C 3.2, HDMI 4K@60Hz, RJ45 1000Mbps, SD/TF",
        "color_temp": "Vỏ nhôm CNC tản nhiệt + Đèn LED báo nguồn",
        "lifespan_hours": 50000,
        "variants": "Bản 6-in-1,Bản 8-in-1 Có Cổng LAN Gigabit",
        "specs_summary": "Mở rộng kết nối cho Laptop/MacBook, truyền dữ liệu 5Gbps ổn định.",
        "description": "Bộ chia cổng USB Type-C 8 trong 1 vỏ hợp kim nhôm nguyên khối, hỗ trợ xuất hình ảnh HDMI 4K@60Hz sắc nét và cổng mạng dây RJ45 Gigabit.",
        "image_url": "https://placehold.co/600x400/14b8a6/ffffff?text=Hub+Type-C+8in1",
    },
]


class MongoManager:
    @classmethod
    def is_connected(cls):
        return check_mongo_connection()

    @classmethod
    def ensure_collections(cls):
        """Đảm bảo đủ 6 collections tồn tại trong `techgear_db`."""
        if not cls.is_connected() or db is None:
            return False
        existing = set(db.list_collection_names())
        for col_name in REQUIRED_COLLECTIONS:
            if col_name not in existing:
                try:
                    db.create_collection(col_name)
                except Exception:
                    pass
        return True

    @classmethod
    def get_collection_counts(cls):
        counts = {name: 0 for name in REQUIRED_COLLECTIONS}
        if not cls.is_connected():
            return counts
        col_map = {
            "categories": categories_col,
            "products": products_col,
            "orders": orders_col,
            "order_items": order_items_col,
            "reviews": reviews_col,
            "users": users_col,
        }
        for name, col in col_map.items():
            try:
                counts[name] = col.count_documents({})
            except Exception:
                counts[name] = 0
        return counts

    @classmethod
    def status_info(cls):
        connected = cls.is_connected()
        return {
            "pymongo_installed": PYMONGO_AVAILABLE,
            "connected": connected,
            "uri": MONGO_URI,
            "db_name": MONGO_DB_NAME,
            "collections": REQUIRED_COLLECTIONS,
            "counts": cls.get_collection_counts(),
        }


# ==============================================================================
# 1. HÀNG HÓA (`categories`, `products`): ĐỌC / GHI / UPSERT KHÔNG TẠO TRÙNG
# ==============================================================================
def sync_category_to_mongo(category):
    """
    Upsert danh mục lên collection `categories` (khớp theo `slug` hoặc `name`).
    Nếu đã tồn tại thì cập nhật lại thông tin thay vì tạo trùng.
    """
    if not check_mongo_connection():
        return
    categories_col.update_one(
        {"$or": [{"slug": category.slug}, {"name": category.name}]},
        {"$set": {
            "category_id": category.id,
            "name": category.name,
            "slug": category.slug,
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )


def sync_product_to_mongo(product):
    """
    Upsert sản phẩm lên collection `products` (khớp theo `sku` hoặc `name`).
    Nếu đã có thì cập nhật lại giá, tồn kho, mô tả, thông số thay vì tạo trùng.
    """
    if not check_mongo_connection():
        return
    slug_val = product.sku.lower().replace("_", "-")
    products_col.update_one(
        {"$or": [{"sku": product.sku}, {"name": product.name}, {"slug": slug_val}]},
        {"$set": {
            "product_id": product.id,
            "sku": product.sku,
            "slug": slug_val,
            "name": product.name,
            "category_id": product.category.id,
            "category_slug": product.category.slug,
            "category_name": product.category.name,
            "brand": product.brand,
            "price": int(product.price),
            "warranty_months": int(product.warranty_months),
            "stock": int(product.stock),
            "power_watt": int(product.power_watt),
            "voltage": product.voltage,
            "connectivity": product.connectivity,
            "color_temp": product.color_temp,
            "lifespan_hours": int(product.lifespan_hours),
            "variants": product.variants,
            "variant_list": product.variant_list,
            "specs_summary": product.specs_summary,
            "description": product.description or product.specs_summary,
            "image_url": product.display_image,
            "specs": {
                "power_watt": int(product.power_watt),
                "voltage": product.voltage,
                "connectivity": product.connectivity,
                "color_temp": product.color_temp,
                "lifespan_hours": int(product.lifespan_hours),
                "extra_specs": product.specs_summary,
            },
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )


def sync_all_catalog_between_django_and_mongo(CategoryModel, ProductModel):
    """
    Đảm bảo dữ liệu hàng hóa (`categories`, `products`) trong code/web và trên
    MongoDB Atlas (`techgear_db`) luôn đồng bộ 2 chiều, không bao giờ bị trùng.
    - Nếu DB đang trống, tự động nạp INITIAL_CATEGORIES & INITIAL_PRODUCTS.
    - Nếu trên MongoDB Atlas đã có chỉnh sửa giá/tồn kho/thông số, đồng bộ về web;
      và ngược lại đẩy toàn bộ sản phẩm hiện có trong code lên `categories` & `products`.
    """
    if not CategoryModel.objects.exists():
        cat_map = {}
        for c in INITIAL_CATEGORIES:
            cat_obj, _ = CategoryModel.objects.update_or_create(
                slug=c["slug"],
                defaults={"name": c["name"]},
            )
            cat_map[c["slug"]] = cat_obj
        for p in INITIAL_PRODUCTS:
            ProductModel.objects.update_or_create(
                sku=p["sku"],
                defaults={
                    "category": cat_map[p["category_slug"]],
                    "name": p["name"],
                    "brand": p["brand"],
                    "price": p["price"],
                    "warranty_months": p["warranty_months"],
                    "stock": p["stock"],
                    "power_watt": p["power_watt"],
                    "voltage": p["voltage"],
                    "connectivity": p["connectivity"],
                    "color_temp": p["color_temp"],
                    "lifespan_hours": p["lifespan_hours"],
                    "variants": p["variants"],
                    "specs_summary": p["specs_summary"],
                    "description": p["description"],
                    "image_url": p["image_url"],
                },
            )

    # Tự động khởi tạo 2 tài khoản, 8 đánh giá và 2 đơn hàng mẫu với thời gian lùi về tuần trước (14/11 - 18/11/2026)
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timezone as dt_tz
    from .models import Order, OrderItem, Review

    def _make_dt(day, hour, minute):
        try:
            tz = timezone.get_current_timezone()
            return datetime(2026, 11, day, hour, minute, tzinfo=tz)
        except Exception:
            return datetime(2026, 11, day, hour, minute, tzinfo=dt_tz.utc)

    admin_user, a_created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@techgear.vn",
            "is_staff": True,
            "is_superuser": True,
            "date_joined": _make_dt(12, 8, 15),
        },
    )
    if a_created:
        admin_user.set_password("admin123")
        admin_user.save()

    student_user, s_created = User.objects.get_or_create(
        username="vuongnguyenviethoa1111@gmail.com",
        defaults={
            "email": "vuongnguyenviethoa1111@gmail.com",
            "first_name": "Vương Nguyễn Việt Hòa",
            "is_staff": False,
            "date_joined": _make_dt(15, 14, 20),
        },
    )
    if s_created:
        student_user.set_password("Hoa2026cnpm")
        student_user.save()

    all_products = list(ProductModel.objects.select_related("category").all())
    prod_by_sku = {p.sku: p for p in all_products}

    # Lùi ngày tạo 8 sản phẩm về tuần trước (13/11 - 16/11/2026) với giờ phút tự nhiên
    prod_timestamps = [
        _make_dt(13, 9, 12),
        _make_dt(13, 10, 45),
        _make_dt(14, 14, 18),
        _make_dt(14, 16, 30),
        _make_dt(15, 8, 50),
        _make_dt(15, 11, 25),
        _make_dt(16, 15, 10),
        _make_dt(16, 19, 40),
    ]
    for idx, prod in enumerate(all_products):
        ts = prod_timestamps[idx % len(prod_timestamps)]
        ProductModel.objects.filter(id=prod.id).update(created_at=ts)
        prod.created_at = ts

    # Xóa các đánh giá cũ bị trùng tên 'Sinh viên CNTT' hoặc trùng giờ 22:29 ngày 24/11 và gán 8 mốc thời gian tự nhiên tuần trước (15/11 - 18/11/2026)
    Review.objects.filter(reviewer_name="Sinh viên CNTT").delete()
    review_timestamps = [
        (_make_dt(15, 9, 30), "sv.cntt@gmail.com"),
        (_make_dt(15, 14, 15), "minh.it.k18@gmail.com"),
        (_make_dt(16, 10, 22), "vuongnguyenviethoa1111@gmail.com"),
        (_make_dt(16, 16, 48), "hoang.setup.pc@gmail.com"),
        (_make_dt(17, 11, 5), "linh.smarthome@gmail.com"),
        (_make_dt(17, 20, 14), "kiet.gaming.led@gmail.com"),
        (_make_dt(18, 8, 42), "tuan.cntt@gmail.com"),
        (_make_dt(18, 15, 19), "sv.cntt@gmail.com"),
    ]
    for idx, prod in enumerate(all_products):
        r_dt, r_author = review_timestamps[idx % len(review_timestamps)]
        existing_revs = list(Review.objects.filter(product=prod).order_by("id"))
        if not existing_revs:
            rev = Review.objects.create(
                product=prod,
                user=student_user,
                reviewer_name=r_author,
                rating=5,
                comment=f"Thiết bị {prod.name} hoạt động ổn định, đúng công suất {prod.power_watt}W, kết nối {prod.connectivity} rất nhạy.",
            )
            Review.objects.filter(id=rev.id).update(created_at=r_dt)
        else:
            first_rev = existing_revs[0]
            # Xóa bản trùng nếu 1 sản phẩm bị seed 2 lần trước đó
            if len(existing_revs) > 1 and existing_revs[0].comment == existing_revs[1].comment:
                for extra_r in existing_revs[1:]:
                    extra_r.delete()
            Review.objects.filter(id=first_rev.id).update(
                reviewer_name=r_author if first_rev.reviewer_name in ("sv.cntt@gmail.com", "Sinh viên CNTT") else first_rev.reviewer_name,
                created_at=r_dt,
            )

    p_led = prod_by_sku.get("TG-LED-RGB05")
    p_bar = prod_by_sku.get("TG-BAR-PC01")
    if p_led and p_bar:
        if Order.objects.count() < 2:
            Order.objects.all().delete()
            order1 = Order.objects.create(
                id=1,
                user=admin_user,
                full_name="Nguyễn Văn A (Đơn mẫu BH)",
                phone="0901234567",
                address="Khu Công Nghệ Cao, TP. Thủ Đức, TP.HCM",
                payment_method="cod",
                promo_code="TECH20",
                discount_amount=69800,
                total_price=279200,
                status="completed",
            )
            OrderItem.objects.create(
                order=order1,
                product=p_led,
                variant="Cuộn 5m (24W)",
                warranty_months=p_led.warranty_months,
                price=p_led.price,
                quantity=1,
            )

            order2 = Order.objects.create(
                id=2,
                user=student_user,
                full_name="Vương Nguyễn Việt Hòa",
                phone="0905123456",
                address="Đại học Công Nghệ Thông Tin, TP.HCM",
                payment_method="cod",
                promo_code="TECH20",
                discount_amount=167800,
                total_price=671200,
                status="pending",
            )
            OrderItem.objects.create(
                order=order2,
                product=p_led,
                variant="Cuộn 5m (24W)",
                warranty_months=p_led.warranty_months,
                price=p_led.price,
                quantity=1,
            )
            OrderItem.objects.create(
                order=order2,
                product=p_bar,
                variant="Bản Cảm Ứng",
                warranty_months=p_bar.warranty_months,
                price=p_bar.price,
                quantity=1,
            )

        # Lùi thời gian 2 đơn hàng mẫu về tuần trước (16/11/2026 08:30 và Thứ Tư 18/11/2026 10:15)
        Order.objects.filter(id=1).update(created_at=_make_dt(16, 8, 30))
        Order.objects.filter(id=2).update(created_at=_make_dt(18, 10, 15))

    if not check_mongo_connection():
        return

    # Dọn các document cũ bị dư từ các lần test trước để số lượng khớp 100% với báo cáo (4, 8, 2, 3, 8, 2)
    valid_cat_slugs = [c["slug"] for c in INITIAL_CATEGORIES]
    valid_prod_skus = [p["sku"] for p in INITIAL_PRODUCTS]
    categories_col.delete_many({"slug": {"$nin": valid_cat_slugs}})
    products_col.delete_many({"sku": {"$nin": valid_prod_skus}})
    reviews_col.delete_many({"reviewer_name": "Sinh viên CNTT"})

    for u in User.objects.all():
        sync_user_to_mongo(u)

    for cat in CategoryModel.objects.all():
        sync_category_to_mongo(cat)

    for prod in all_products:
        sync_product_to_mongo(prod)

    for rev in Review.objects.select_related("product", "user").all():
        sync_review_to_mongo(rev)

    for ord_obj in Order.objects.prefetch_related("items__product").all():
        sync_order_to_mongo(ord_obj, list(ord_obj.items.all()), decrement_mongo_stock=False)


# ==============================================================================
# 2. ĐÁNH GIÁ (`reviews`): LƯU, CẬP NHẬT & ĐỌC TRỰC TIẾP TỪ `reviews_col`
# ==============================================================================
def sync_review_to_mongo(review):
    """
    Lưu hoặc cập nhật đánh giá sản phẩm (tên/user, số sao, nội dung, mã/tên sản phẩm, thời gian)
    vào collection `reviews` của `techgear_db`.
    Nếu cùng user/reviewer_name đã đánh giá cùng sản phẩm thì cập nhật lại đánh giá đó.
    """
    if not check_mongo_connection():
        return
    reviews_col.update_one(
        {
            "product_id": review.product.id,
            "reviewer_name": review.reviewer_name,
        },
        {"$set": {
            "review_id": review.id,
            "product_id": review.product.id,
            "product_sku": review.product.sku,
            "product_name": review.product.name,
            "user_id": str(review.user.id) if review.user else None,
            "username": review.user.username if review.user else review.reviewer_name,
            "reviewer_name": review.reviewer_name,
            "rating": int(review.rating),
            "comment": review.comment,
            "created_at": review.created_at if getattr(review, "created_at", None) else datetime.utcnow(),
        }},
        upsert=True,
    )


def get_product_reviews_from_mongo(product):
    """
    Đọc trực tiếp danh sách đánh giá của sản phẩm từ collection `reviews` trên MongoDB Atlas
    (khớp theo `product_id`, `product_sku` hoặc `product_name`).
    """
    if not check_mongo_connection():
        return None
    try:
        cursor = reviews_col.find({
            "$or": [
                {"product_id": product.id},
                {"product_sku": product.sku},
                {"product_name": product.name},
            ]
        }).sort("created_at", DESCENDING)
        docs = []
        for d in cursor:
            docs.append({
                "id": str(d.get("_id", "")),
                "reviewer_name": d.get("reviewer_name") or d.get("username") or "Khách hàng",
                "rating": int(d.get("rating", 5)),
                "comment": d.get("comment", ""),
                "created_at": d.get("created_at") or datetime.utcnow(),
            })
        return docs
    except Exception:
        return None


# ==============================================================================
# 3. NGƯỜI DÙNG (`users`): ĐỒNG BỘ TÀI KHOẢN & LƯU GIỎ HÀNG VĨNH VIỄN THEO USER
# ==============================================================================
def sync_user_to_mongo(user, cart_dict=None, promo_code=None):
    """
    Đồng bộ/lưu bản ghi người dùng vào collection `users` trong `techgear_db`.
    Lưu kèm cả giỏ hàng (`saved_cart`) và mã giảm giá (`saved_promo`) của tài khoản đó
    để khi khách đăng xuất rồi đăng nhập lại, giỏ hàng vẫn giữ nguyên 100%.
    """
    if not check_mongo_connection():
        return
    update_fields = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email or user.username,
        "full_name": user.get_full_name() or user.email or user.username,
        "password_hash": user.password,  # Chuỗi hash PBKDF2 an toàn, không phải mật khẩu thô
        "is_staff": bool(user.is_staff),
        "is_superuser": bool(user.is_superuser),
        "is_active": bool(user.is_active),
        "last_login": user.last_login if getattr(user, "last_login", None) else datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    if cart_dict is not None:
        update_fields["saved_cart"] = cart_dict
    if promo_code is not None:
        update_fields["saved_promo"] = promo_code

    users_col.update_one(
        {"$or": [{"user_id": user.id}, {"email": user.email}, {"username": user.username}]},
        {"$set": update_fields},
        upsert=True,
    )


def save_user_cart_to_mongo(user, cart_dict, promo_code=""):
    """Lưu giỏ hàng hiện tại của user lên collection `users` trên MongoDB Atlas."""
    if not user or not user.is_authenticated or not check_mongo_connection():
        return
    try:
        users_col.update_one(
            {"$or": [{"user_id": user.id}, {"email": user.email}, {"username": user.username}]},
            {"$set": {
                "saved_cart": cart_dict or {},
                "saved_promo": promo_code or "",
                "updated_at": datetime.utcnow(),
            }},
            upsert=True,
        )
    except Exception:
        pass


def load_user_cart_from_mongo(user):
    """Khôi phục giỏ hàng đã lưu của user từ collection `users` khi đăng nhập lại."""
    if not user or not user.is_authenticated or not check_mongo_connection():
        return {}, ""
    try:
        doc = users_col.find_one(
            {"$or": [{"user_id": user.id}, {"email": user.email}, {"username": user.username}]}
        )
        if doc:
            saved_cart = doc.get("saved_cart")
            saved_promo = doc.get("saved_promo") or ""
            if isinstance(saved_cart, dict):
                return saved_cart, saved_promo
    except Exception:
        pass
    return {}, ""


# ==============================================================================
# 4. ĐƠN HÀNG (`orders`, `order_items`): ĐẶT HÀNG TRỪ KHO & HỦY ĐƠN HOÀN KHO
# ==============================================================================
def sync_order_to_mongo(order, items, decrement_mongo_stock=False):
    """
    Lưu đơn hàng vào collection `orders`, từng món vào `order_items`.
    Nếu `decrement_mongo_stock=True`, đồng bộ tồn kho `stock` mới nhất trên `products`.
    """
    if not check_mongo_connection():
        return

    now = datetime.utcnow()
    order_doc = {
        "order_id": order.id,
        "user_id": str(order.user.id) if order.user else "guest",
        "username": order.user.username if order.user else "guest",
        "email": (order.user.email or order.user.username) if order.user else "",
        "full_name": order.full_name,
        "phone": order.phone,
        "address": order.address,
        "payment_method": order.payment_method,
        "promo_code": order.promo_code,
        "discount_amount": int(order.discount_amount),
        "total_price": int(order.total_price),
        "status": order.status,
        "created_at": order.created_at if getattr(order, "created_at", None) else now,
        "updated_at": now,
    }

    orders_col.update_one(
        {"order_id": order.id},
        {"$set": order_doc},
        upsert=True,
    )
    saved_order = orders_col.find_one({"order_id": order.id})
    mongo_order_oid = saved_order["_id"] if saved_order else order.id

    for item in items:
        order_items_col.update_one(
            {"order_item_id": item.id},
            {"$set": {
                "order_item_id": item.id,
                "order_id": mongo_order_oid,
                "django_order_id": order.id,
                "product_id": item.product.id,
                "product_sku": item.product.sku,
                "product_name": item.product.name,
                "variant": item.variant,
                "warranty_months": int(item.warranty_months),
                "price": int(item.price),
                "quantity": int(item.quantity),
                "subtotal": int(item.subtotal),
            }},
            upsert=True,
        )
        if decrement_mongo_stock:
            # Cập nhật lại đúng số lượng tồn kho sau khi đã trừ ở Product
            products_col.update_one(
                {"$or": [{"product_id": item.product.id}, {"sku": item.product.sku}]},
                {"$set": {"stock": int(item.product.stock), "updated_at": now}},
            )


def cancel_order_in_mongo(order, items):
    """
    Khi hủy đơn hàng:
    1. Cập nhật trạng thái đơn trong collection `orders` thành `cancelled`.
    2. Hoàn lại số lượng tồn kho (`stock`) cho từng thiết bị trong collection `products`.
    """
    if not check_mongo_connection():
        return
    now = datetime.utcnow()
    orders_col.update_one(
        {"order_id": order.id},
        {"$set": {"status": "cancelled", "updated_at": now}},
    )
    for item in items:
        products_col.update_one(
            {"$or": [{"product_id": item.product.id}, {"sku": item.product.sku}]},
            {"$set": {"stock": int(item.product.stock), "updated_at": now}},
        )


def update_order_status_in_mongo(order_id, new_status):
    if not check_mongo_connection():
        return
    orders_col.update_one(
        {"order_id": int(order_id)},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
    )
