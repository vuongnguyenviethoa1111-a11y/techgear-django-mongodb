from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from .models import Category, Product, Order, OrderItem, Review
from mongo_db import (
    ObjectId,
    check_mongo_connection,
    categories_col,
    order_items_col,
    orders_col,
    products_col,
    reviews_col,
    users_col,
)
from .mongo_client import (
    MongoManager,
    sync_all_catalog_between_django_and_mongo,
    sync_category_to_mongo,
    sync_product_to_mongo,
    sync_order_to_mongo,
    cancel_order_in_mongo,
    update_order_status_in_mongo,
    sync_review_to_mongo,
    get_product_reviews_from_mongo,
    sync_user_to_mongo,
)

VALID_PROMOS = {
    'TECH20': 0.20,    # Giảm 20% cho đơn phụ kiện & đèn LED
    'SMART10': 0.10,   # Giảm 10% cho thiết bị thông minh
}

_CATALOG_SYNCED_ONCE = False


def _ensure_catalog_synced():
    """Tự động đẩy dữ liệu hàng hóa & 2 đơn hàng mẫu lên `techgear_db` ngay khi mở trang."""
    global _CATALOG_SYNCED_ONCE
    if not _CATALOG_SYNCED_ONCE or not Category.objects.exists() or Order.objects.count() < 2:
        sync_all_catalog_between_django_and_mongo(Category, Product)
        _CATALOG_SYNCED_ONCE = True


def _build_cart_data(request):
    """Đọc dữ liệu giỏ hàng từ request.session['cart'] và tính tổng tiền, giảm giá."""
    raw_cart = request.session.get('cart', {})
    promo_code = request.session.get('promo_code', '')
    items = []
    subtotal = 0

    keys_to_remove = []
    for key, data in raw_cart.items():
        product_id = data.get('product_id')
        variant = data.get('variant', 'Bản Tiêu Chuẩn')
        quantity = int(data.get('quantity', 1))
        product = Product.objects.filter(id=product_id).first()
        if not product:
            keys_to_remove.append(key)
            continue
        line_total = product.price * quantity
        subtotal += line_total
        items.append({
            'key': key,
            'product': product,
            'variant': variant,
            'warranty_months': product.warranty_months,
            'quantity': quantity,
            'line_total': line_total,
        })

    if keys_to_remove:
        for k in keys_to_remove:
            raw_cart.pop(k, None)
        request.session['cart'] = raw_cart
        request.session.modified = True

    discount_rate = VALID_PROMOS.get(promo_code, 0.0)
    discount_amount = int(round(subtotal * discount_rate))
    final_total = max(0, subtotal - discount_amount)

    return {
        'items': items,
        'subtotal': subtotal,
        'promo_code': promo_code,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }


def _calculate_led_power(area_m2, room_type):
    """Công cụ tính công suất đèn LED & gợi ý thiết bị thông minh theo diện tích phòng (m2)."""
    factor_map = {
        'bedroom': (1.2, 'Phòng ngủ / Góc chill (Ánh sáng ấm 3000K - RGB dịu mắt)'),
        'work': (1.8, 'Phòng làm việc / Góc Setup PC - Gaming (Ánh sáng trung tính 4500K - 6500K)'),
        'living': (2.2, 'Phòng khách / Studio sáng tạo (Độ sáng cao + Đồng bộ nhạc Smart Wi-Fi)'),
    }
    factor, room_label = factor_map.get(room_type, factor_map['work'])
    recommended_watt = max(5, int(round(area_m2 * factor)))
    lumens = recommended_watt * 95

    if recommended_watt <= 12:
        suggestion = "Phù hợp Đèn bàn LED chống cận, Đèn ngủ cảm biến hoặc Dây LED RGB 2m-5m (5W - 12W)."
    elif recommended_watt <= 25:
        suggestion = "Phù hợp Thanh LED Màn Hình + Bóng LED Wi-Fi Smart Bulb hoặc Đèn Ambiance đổi màu (15W - 24W)."
    else:
        suggestion = "Phù hợp Hệ thống Đèn ốp trần thông minh 36W kết hợp Dây LED RGBIC đồng bộ âm thanh và Ổ cắm Wi-Fi."

    return {
        'area': area_m2,
        'room_type': room_type,
        'room_label': room_label,
        'recommended_watt': recommended_watt,
        'lumens': lumens,
        'suggestion': suggestion,
    }


def home(request):
    """
    Trang chủ:
    - Tự động đồng bộ hàng hóa lên `categories` và `products` trên MongoDB Atlas (`techgear_db`).
    - Lọc theo danh mục, tìm kiếm từ khóa và sắp xếp giá/bảo hành.
    """
    _ensure_catalog_synced()

    categories = Category.objects.all()
    products = Product.objects.select_related('category').all()

    query = request.GET.get('q', '').strip()
    selected_cat = request.GET.get('category', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__icontains=query) |
            Q(connectivity__icontains=query) |
            Q(specs_summary__icontains=query)
        )

    if selected_cat:
        products = products.filter(category__slug=selected_cat)

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'warranty_desc':
        products = products.order_by('-warranty_months', 'price')
    else:
        products = products.order_by('-created_at')

    power_result = None
    area_str = request.GET.get('area', '').strip()
    room_type = request.GET.get('room_type', 'work').strip()
    if area_str:
        try:
            area_val = float(area_str)
            if 2 <= area_val <= 150:
                power_result = _calculate_led_power(area_val, room_type)
        except ValueError:
            pass

    context = {
        'categories': categories,
        'products': products,
        'query': query,
        'selected_cat': selected_cat,
        'sort': sort,
        'power_result': power_result,
        'mongo_info': MongoManager.status_info(),
    }
    return render(request, 'shop/home.html', context)


@csrf_exempt
def product_detail(request, product_id):
    """
    Trang chi tiết thiết bị & Đánh giá (`reviews`):
    - Khi gửi form đánh giá: lưu/cập nhật (upsert) trực tiếp vào collection `reviews` trong `techgear_db`.
    - Đọc danh sách đánh giá từ `reviews` trên MongoDB Atlas để hiển thị trên trang sản phẩm.
    """
    _ensure_catalog_synced()
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:3]

    if request.method == 'POST':
        rating = max(1, min(5, int(request.POST.get('rating', 5))))
        comment = request.POST.get('comment', '').strip()
        reviewer_name = (
            (request.user.email or request.user.username)
            if request.user.is_authenticated
            else request.POST.get('reviewer_name', 'Khách hàng').strip()
        ) or 'Khách mua hàng'

        if comment:
            # Nếu người dùng này đã đánh giá sản phẩm này trước đó thì cập nhật lại, ngược lại tạo mới
            rev, created = Review.objects.update_or_create(
                product=product,
                reviewer_name=reviewer_name,
                defaults={
                    'user': request.user if request.user.is_authenticated else None,
                    'rating': rating,
                    'comment': comment,
                },
            )
            # Lưu / cập nhật trực tiếp lên collection `reviews` trên MongoDB Atlas (`techgear_db`)
            sync_review_to_mongo(rev)
            if created:
                messages.success(request, "Đã lưu đánh giá kỹ thuật vào collection 'reviews' (techgear_db)!")
            else:
                messages.success(request, "Đã cập nhật đánh giá kỹ thuật của bạn trên collection 'reviews' (techgear_db)!")
            return redirect('product_detail', product_id=product.id)

    # Ưu tiên lấy danh sách đánh giá trực tiếp từ collection `reviews` của MongoDB Atlas
    mongo_reviews = get_product_reviews_from_mongo(product)
    reviews = mongo_reviews if mongo_reviews else list(product.reviews.all())

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'reviews_count': len(reviews),
    })


@csrf_exempt
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập tài khoản trước khi mua hàng và thêm thiết bị vào giỏ.")
        return redirect(f"/login/?next={request.META.get('HTTP_REFERER', '/')}")

    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        variant = request.POST.get('variant', 'Bản Tiêu Chuẩn').strip()
        try:
            quantity = max(1, int(request.POST.get('quantity', 1)))
        except ValueError:
            quantity = 1

        cart = request.session.get('cart', {})
        key = f"{product.id}_{variant}"
        current_qty = cart.get(key, {}).get('quantity', 0)

        if current_qty + quantity > product.stock:
            messages.warning(request, f"Số lượng yêu cầu vượt quá tồn kho hiện có ({product.stock} sản phẩm).")
            return redirect('home')

        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {
                'product_id': product.id,
                'variant': variant,
                'quantity': quantity,
            }

        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f"Đã thêm {product.name} ({variant} • BH {product.warranty_months} tháng) vào giỏ hàng.")
    return redirect('view_cart')


def view_cart(request):
    cart_data = _build_cart_data(request)
    return render(request, 'shop/cart.html', {'cart': cart_data})


@csrf_exempt
def update_cart(request, item_key):
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập để thao tác với giỏ hàng.")
        return redirect('login')
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        action = request.POST.get('action')
        if item_key in cart:
            product = Product.objects.filter(id=cart[item_key].get('product_id')).first()
            if action == 'inc':
                if product and cart[item_key]['quantity'] + 1 > product.stock:
                    messages.warning(request, f"Thiết bị {product.name} chỉ còn tối đa {product.stock} chiếc trong kho.")
                else:
                    cart[item_key]['quantity'] += 1
            elif action == 'dec':
                cart[item_key]['quantity'] -= 1
                if cart[item_key]['quantity'] <= 0:
                    cart.pop(item_key, None)
            elif action == 'remove':
                cart.pop(item_key, None)
            request.session['cart'] = cart
            request.session.modified = True
    return redirect('view_cart')


@csrf_exempt
def apply_promo(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập để áp dụng mã giảm giá.")
        return redirect('login')
    if request.method == 'POST':
        code = request.POST.get('promo_code', '').strip().upper()
        if code in VALID_PROMOS:
            request.session['promo_code'] = code
            percent = int(VALID_PROMOS[code] * 100)
            messages.success(request, f"Đã áp dụng mã {code} (giảm {percent}% tổng đơn thiết bị).")
        else:
            request.session['promo_code'] = ''
            messages.warning(request, "Mã giảm giá không hợp lệ. Thử mã TECH20 hoặc SMART10.")
        request.session.modified = True
    return redirect('view_cart')


@csrf_exempt
def checkout(request):
    """
    Đặt hàng (`orders`, `order_items`, `products`):
    - Bắt buộc đăng nhập.
    - Lưu đơn hàng vào `orders`, từng món vào `order_items`.
    - Trừ `stock` của từng sản phẩm ở cả Django và collection `products` trên MongoDB Atlas (`techgear_db`).
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Bạn cần đăng nhập tài khoản để tiến hành đặt mua thiết bị và kích hoạt bảo hành.")
        return redirect('/login/?next=/checkout/')

    cart_data = _build_cart_data(request)
    if not cart_data['items']:
        messages.warning(request, "Giỏ hàng đang trống, vui lòng chọn thiết bị trước khi đặt hàng.")
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        payment_method = request.POST.get('payment_method', 'cod').strip()

        if not full_name or not phone or not address:
            messages.warning(request, "Vui lòng điền đầy đủ họ tên, số điện thoại kích hoạt bảo hành và địa chỉ.")
            return render(request, 'shop/checkout.html', {'cart': cart_data})

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            payment_method=payment_method,
            promo_code=cart_data['promo_code'],
            discount_amount=cart_data['discount_amount'],
            total_price=cart_data['final_total'],
        )

        created_items = []
        for item in cart_data['items']:
            product = item['product']
            qty = item['quantity']
            if product.stock >= qty:
                product.stock -= qty
                product.save()
            oi = OrderItem.objects.create(
                order=order,
                product=product,
                variant=item['variant'],
                warranty_months=product.warranty_months,
                price=product.price,
                quantity=qty,
            )
            created_items.append(oi)

        # Lưu đơn vào `orders`, từng món vào `order_items` và cập nhật `stock` đã trừ trên `products`
        sync_order_to_mongo(order, created_items, decrement_mongo_stock=True)

        request.session['cart'] = {}
        request.session['promo_code'] = ''
        request.session.modified = True

        messages.success(request, f"Đặt hàng thành công! Mã đơn #{order.id} đã lưu vào techgear_db (orders, order_items & trừ kho products).")
        return redirect('my_orders')

    return render(request, 'shop/checkout.html', {'cart': cart_data})


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'shop/my_orders.html', {'orders': orders})


@csrf_exempt
@login_required(login_url='login')
def cancel_order(request, order_id):
    """
    Hủy đơn hàng:
    - Cập nhật trạng thái đơn thành `cancelled` trong `orders`.
    - Hoàn lại số lượng `stock` cho từng sản phẩm trong `products` trên cả Django và MongoDB Atlas (`techgear_db`).
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()

            order_items = list(order.items.select_related('product').all())
            for item in order_items:
                item.product.stock += item.quantity
                item.product.save()

            # Cập nhật trạng thái `cancelled` trong `orders` và hoàn kho trong `products` trên MongoDB Atlas
            cancel_order_in_mongo(order, order_items)

            messages.info(request, f"Đã hủy đơn hàng #{order.id}, cập nhật trạng thái và hoàn lại tồn kho trên techgear_db.")
        else:
            messages.warning(request, "Chỉ có thể hủy đơn hàng khi đang ở trạng thái 'Chờ xác nhận'.")
    return redirect('my_orders')


def warranty_check(request):
    """Tra cứu bảo hành điện tử theo Số điện thoại hoặc Mã đơn hàng."""
    keyword = request.GET.get('q', '').strip()
    matched_orders = []
    if keyword:
        if keyword.isdigit():
            matched_orders = Order.objects.filter(
                Q(phone__icontains=keyword) | Q(id=int(keyword))
            ).prefetch_related('items__product')
        else:
            matched_orders = Order.objects.filter(phone__icontains=keyword).prefetch_related('items__product')
    return render(request, 'shop/warranty_check.html', {
        'keyword': keyword,
        'matched_orders': matched_orders,
    })


def dashboard_report(request):
    """Trang thống kê tồn kho, doanh thu và số lượng document trong 6 collections của `techgear_db`."""
    _ensure_catalog_synced()
    total_products = Product.objects.count()
    total_stock = Product.objects.aggregate(s=Sum('stock'))['s'] or 0
    low_stock_products = Product.objects.filter(stock__lte=10).order_by('stock')
    total_orders = Order.objects.count()
    active_orders = Order.objects.exclude(status='cancelled')
    total_revenue = active_orders.aggregate(r=Sum('total_price'))['r'] or 0
    total_reviews = Review.objects.count()

    return render(request, 'shop/dashboard.html', {
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_products': low_stock_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_reviews': total_reviews,
        'mongo_info': MongoManager.status_info(),
    })


@csrf_exempt
def login_view(request):
    """Đăng nhập và đồng bộ thông tin tài khoản vào collection `users` của `techgear_db`."""
    next_url = request.GET.get('next') or request.POST.get('next') or 'home'
    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        auth_username = login_input
        matched_user = User.objects.filter(email__iexact=login_input).first()
        if matched_user:
            auth_username = matched_user.username

        user = authenticate(request, username=auth_username, password=password)
        if user is not None:
            login(request, user)
            # Đồng bộ thông tin đăng nhập (last_login, email, hash password) lên collection `users`
            sync_user_to_mongo(user)
            messages.success(request, f"Chào mừng {user.email or user.username} đến với TechGear Smart & LED.")
            return redirect(next_url)
        messages.warning(request, "Email hoặc mật khẩu không đúng.")
    return render(request, 'shop/login.html', {'next': next_url})


@csrf_exempt
def register_view(request):
    """Đăng ký tài khoản bằng Gmail + 2 lần mật khẩu và lưu bản ghi vào collection `users` của `techgear_db`."""
    next_url = request.GET.get('next') or request.POST.get('next') or 'home'
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not email:
            messages.warning(request, "Vui lòng nhập địa chỉ Gmail / Email của bạn.")
        elif password != confirm_password:
            messages.warning(request, "Mật khẩu nhập lại không khớp.")
        elif User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            messages.warning(request, "Email này đã được đăng ký tài khoản.")
        else:
            user = User.objects.create_user(username=email, email=email, password=password)
            # Lưu tài khoản mới trực tiếp vào collection `users` (kèm password_hash an toàn)
            sync_user_to_mongo(user)
            login(request, user)
            messages.success(request, f"Đăng ký thành công! Đã lưu tài khoản {user.email} vào collection 'users' (techgear_db).")
            return redirect(next_url)
    return render(request, 'shop/register.html', {'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "Bạn đã đăng xuất khỏi hệ thống.")
    return redirect('home')
