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
    save_user_cart_to_mongo,
    load_user_cart_from_mongo,
)

VALID_PROMOS = {
    'TECH20': 0.20,    # Giảm 20% cho đơn phụ kiện & đèn LED
    'SMART10': 0.10,   # Giảm 10% cho thiết bị thông minh
}

_CATALOG_SYNCED_ONCE = False


def _ensure_catalog_synced():
    """
    Chỉ kiểm tra trên SQLite nội bộ (< 2ms). Nếu thiếu dữ liệu mới nạp,
    còn việc đẩy đồng bộ lên MongoDB Atlas sẽ chạy ngầm trong background thread.
    """
    global _CATALOG_SYNCED_ONCE
    if _CATALOG_SYNCED_ONCE:
        return
    _CATALOG_SYNCED_ONCE = True
    needs_img_sync = Product.objects.filter(
        Q(image_url__icontains='placehold.co') |
        Q(sku='TG-HUB-8IN1', image_url__startswith='/static/') |
        Q(sku='TG-HUB-8IN1', image_url__icontains='unsplash.com')
    ).exists()
    if not Category.objects.exists() or Order.objects.count() < 2 or needs_img_sync:
        from .mongo_client import _run_async
        _run_async(sync_all_catalog_between_django_and_mongo, Category, Product)


def _build_cart_data(request):
    """Đọc dữ liệu giỏ hàng từ request.session['cart'] (< 1ms) và tính tổng tiền."""
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
    }
    return render(request, 'shop/home.html', context)


@csrf_exempt
def product_detail(request, product_id):
    """
    Trang chi tiết thiết bị & Đánh giá (`reviews`):
    - Đọc cực nhanh từ SQLite (< 5ms) và đồng bộ đánh giá mới lên `reviews` của `techgear_db` trong luồng nền.
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
            rev, created = Review.objects.update_or_create(
                product=product,
                reviewer_name=reviewer_name,
                defaults={
                    'user': request.user if request.user.is_authenticated else None,
                    'rating': rating,
                    'comment': comment,
                },
            )
            # Đồng bộ ngầm lên collection `reviews` trên MongoDB Atlas (`techgear_db`) không gây chờ trang
            from .mongo_client import _run_async
            _run_async(sync_review_to_mongo, rev)
            if created:
                messages.success(request, "Đã lưu đánh giá kỹ thuật vào collection 'reviews' (techgear_db)!")
            else:
                messages.success(request, "Đã cập nhật đánh giá kỹ thuật của bạn trên collection 'reviews' (techgear_db)!")
            return redirect('product_detail', product_id=product.id)

    reviews = list(product.reviews.all())

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
        # Lưu giỏ hàng vĩnh viễn theo tài khoản lên collection `users` (techgear_db) trong luồng nền
        from .mongo_client import _run_async
        _run_async(save_user_cart_to_mongo, request.user, dict(cart), request.session.get('promo_code', ''))
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
            from .mongo_client import _run_async
            _run_async(save_user_cart_to_mongo, request.user, dict(cart), request.session.get('promo_code', ''))
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
        from .mongo_client import _run_async
        _run_async(save_user_cart_to_mongo, request.user, dict(request.session.get('cart', {})), request.session.get('promo_code', ''))
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

        # Lưu đơn vào `orders`, từng món vào `order_items` và cập nhật `stock` đã trừ trên `products` trong luồng nền
        from .mongo_client import _run_async
        _run_async(sync_order_to_mongo, order, created_items, True)

        request.session['cart'] = {}
        request.session['promo_code'] = ''
        request.session.modified = True
        # Xóa giỏ hàng đã đặt xong trên MongoDB `users`
        _run_async(save_user_cart_to_mongo, request.user, {}, '')

        messages.success(request, f"Đặt hàng thành công! Mã đơn #{order.id} đã lưu vào techgear_db (orders, order_items & trừ kho products).")
        return redirect('my_orders')

    return render(request, 'shop/checkout.html', {'cart': cart_data})


@login_required(login_url='login')
def my_orders(request):
    """
    Trang Quản lý đơn hàng của khách hàng:
    - Hỗ trợ tìm kiếm / tra cứu đơn hàng theo Mã đơn (#id), Số điện thoại, Họ tên hoặc Tên thiết bị.
    - Hỗ trợ lọc theo trạng thái đơn (`pending`, `shipping`, `completed`, `cancelled`).
    - Cho phép bấm nút 'Hủy đơn hàng & Hoàn kho' trực tiếp khi đơn đang 'Chờ xác nhận' (`pending`).
    """
    _ensure_catalog_synced()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if request.user.is_staff or request.user.is_superuser:
        # Nếu là tài khoản admin hoặc đang demo báo cáo, hiển thị toàn bộ đơn hoặc đơn của user
        orders = Order.objects.all().prefetch_related('items__product')
    else:
        orders = Order.objects.filter(
            Q(user=request.user) | Q(full_name__icontains=request.user.first_name or request.user.username)
        ).prefetch_related('items__product')

    if q:
        clean_id = q.lstrip('#').strip()
        if clean_id.isdigit():
            orders = Order.objects.filter(
                Q(id=int(clean_id)) | Q(phone__icontains=q) | Q(full_name__icontains=q)
            ).prefetch_related('items__product')
        else:
            orders = orders.filter(
                Q(phone__icontains=q) |
                Q(full_name__icontains=q) |
                Q(items__product__name__icontains=q) |
                Q(items__product__sku__icontains=q)
            ).distinct()

    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'shop/my_orders.html', {
        'orders': orders,
        'q': q,
        'status_filter': status_filter,
    })


@csrf_exempt
@login_required(login_url='login')
def cancel_order(request, order_id):
    """
    Hủy đơn hàng:
    - Cập nhật trạng thái đơn thành `cancelled` trong `orders`.
    - Hoàn lại số lượng `stock` cho từng sản phẩm trong `products` trên cả Django và MongoDB Atlas (`techgear_db`).
    """
    if request.method == 'POST':
        if request.user.is_staff or request.user.is_superuser:
            order = get_object_or_404(Order, id=order_id)
        else:
            order = get_object_or_404(Order, id=order_id)
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()

            order_items = list(order.items.select_related('product').all())
            for item in order_items:
                item.product.stock += item.quantity
                item.product.save()

            # Cập nhật trạng thái `cancelled` trong `orders` và hoàn kho trong `products` trên MongoDB Atlas trong luồng nền
            from .mongo_client import _run_async
            _run_async(cancel_order_in_mongo, order, order_items)

            messages.info(request, f"Đã hủy đơn hàng #{order.id}, cập nhật trạng thái 'Đã hủy' và hoàn lại tồn kho trên techgear_db.")
        else:
            messages.warning(request, "Chỉ có thể hủy đơn hàng khi đang ở trạng thái 'Chờ xác nhận'.")
    next_page = request.POST.get('next') or 'my_orders'
    return redirect(next_page)


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


@login_required(login_url='login')
def dashboard_report(request):
    """Trang thống kê tồn kho, doanh thu và số lượng document trong 6 collections của `techgear_db` (Chỉ dành cho Admin)."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.warning(request, "Chỉ tài khoản Quản trị viên (Admin) mới có quyền xem Bảng Thống kê Hệ thống & MongoDB.")
        return redirect('home')
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
    """Đăng nhập, khôi phục giỏ hàng đã lưu từ MongoDB `users` và đồng bộ thông tin tài khoản."""
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
            # Giữ lại các món vừa thêm (nếu có) và gộp với giỏ hàng đã lưu của user trong MongoDB `users`
            pre_login_cart = request.session.get('cart', {})
            pre_login_promo = request.session.get('promo_code', '')

            login(request, user)

            saved_cart, saved_promo = load_user_cart_from_mongo(user)
            merged_cart = dict(saved_cart or {})
            for k, v in (pre_login_cart or {}).items():
                if k in merged_cart:
                    merged_cart[k]['quantity'] = merged_cart[k].get('quantity', 0) + v.get('quantity', 1)
                else:
                    merged_cart[k] = v

            final_promo = pre_login_promo or saved_promo or ''
            request.session['cart'] = merged_cart
            request.session['promo_code'] = final_promo
            request.session.modified = True

            # Đồng bộ thông tin đăng nhập + giỏ hàng lên collection `users` trong luồng nền
            from .mongo_client import _run_async
            _run_async(sync_user_to_mongo, user, merged_cart, final_promo)
            messages.success(request, f"Chào mừng {user.email or user.username} quay trở lại! Đã đồng bộ giỏ hàng của bạn.")
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
            pre_cart = request.session.get('cart', {})
            pre_promo = request.session.get('promo_code', '')
            user = User.objects.create_user(username=email, email=email, password=password)
            login(request, user)
            request.session['cart'] = pre_cart
            request.session['promo_code'] = pre_promo
            request.session.modified = True
            from .mongo_client import _run_async
            _run_async(sync_user_to_mongo, user, pre_cart, pre_promo)
            messages.success(request, f"Đăng ký thành công! Đã lưu tài khoản {user.email} vào collection 'users' (techgear_db).")
            return redirect(next_url)
    return render(request, 'shop/register.html', {'next': next_url})


def logout_view(request):
    """Trước khi đăng xuất, lưu toàn bộ giỏ hàng hiện tại của user vào collection `users` trên MongoDB Atlas."""
    if request.user.is_authenticated:
        current_cart = dict(request.session.get('cart', {}))
        current_promo = request.session.get('promo_code', '')
        from .mongo_client import _run_async
        _run_async(save_user_cart_to_mongo, request.user, current_cart, current_promo)
    logout(request)
    messages.info(request, "Bạn đã đăng xuất. Giỏ hàng của bạn đã được lưu an toàn và sẽ tự khôi phục khi đăng nhập lại.")
    return redirect('home')


@csrf_exempt
@login_required(login_url='login')
def admin_panel(request):
    """
    Trang Quản lý hệ thống dành cho Admin ngay trên giao diện web (/quan-ly/):
    Bao gồm đầy đủ 5 phân hệ trong khối QUẢN LÝ THIẾT BỊ CÔNG NGHỆ & ĐÈN LED (TECHGEAR):
    1. Danh mục thiết bị (categories) - Thêm / Sửa / Xóa
    2. Thiết bị & Đèn LED (products) - Thêm / Sửa (chọn ảnh từ máy hoặc link) / Xóa
    3. Tài khoản người dùng (users) - Thêm / Đổi quyền Staff / Kích hoạt / Xóa
    4. Đánh giá thiết bị (reviews) - Thêm / Sửa / Xóa
    5. Đơn hàng (orders) - Đổi trạng thái đơn (Chờ xác nhận, Đang giao, Đã hoàn thành, Đã hủy) / Xóa
    + Khối Xác thực & Ủy quyền (Các nhóm & Người sử dụng) và Hoạt động gần đây.
    """
    _ensure_catalog_synced()
    if not (request.user.is_staff or request.user.is_superuser):
        messages.warning(request, "Chỉ tài khoản Quản trị viên (Admin) mới có quyền truy cập trang Quản lý hệ thống.")
        return redirect('home')

    from django.contrib.auth.models import Group
    from django.contrib.admin.models import LogEntry
    from .mongo_client import _run_async
    from mongo_db import categories_col, products_col, orders_col, reviews_col, users_col, check_mongo_connection

    active_tab = request.GET.get('tab', 'overview').strip()

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()
        active_tab = request.POST.get('tab', active_tab).strip()

        # 1. QUẢN LÝ DANH MỤC THIẾT BỊ
        if action == 'save_category':
            cat_id = request.POST.get('cat_id', '').strip()
            name = request.POST.get('name', '').strip()
            slug = request.POST.get('slug', '').strip()
            if name and slug:
                if cat_id:
                    cat = get_object_or_404(Category, id=int(cat_id))
                    cat.name = name
                    cat.slug = slug
                    cat.save()
                    messages.success(request, f"Đã cập nhật danh mục '{name}'.")
                else:
                    cat, _ = Category.objects.update_or_create(slug=slug, defaults={'name': name})
                    messages.success(request, f"Đã thêm danh mục mới '{name}'.")
                _run_async(sync_category_to_mongo, cat)

        elif action == 'delete_category':
            cat_id = int(request.POST.get('cat_id', 0))
            cat = Category.objects.filter(id=cat_id).first()
            if cat:
                slug_val = cat.slug
                cat.delete()
                if check_mongo_connection():
                    _run_async(categories_col.delete_one, {'slug': slug_val})
                messages.info(request, "Đã xóa danh mục thiết bị.")

        # 2. QUẢN LÝ THIẾT BỊ & ĐÈN LED
        elif action == 'save_product':
            prod_id = request.POST.get('prod_id', '').strip()
            cat_id = int(request.POST.get('category_id', 0))
            category = get_object_or_404(Category, id=cat_id)
            sku = request.POST.get('sku', 'TG-NEW-01').strip()
            name = request.POST.get('name', '').strip()
            brand = request.POST.get('brand', 'TechGear').strip()
            price = int(request.POST.get('price', 199000) or 199000)
            warranty_months = int(request.POST.get('warranty_months', 12) or 12)
            stock = int(request.POST.get('stock', 20) or 20)
            power_watt = int(request.POST.get('power_watt', 12) or 12)
            voltage = request.POST.get('voltage', '220V / USB-C 5V').strip()
            connectivity = request.POST.get('connectivity', 'Wi-Fi 2.4GHz / Bluetooth').strip()
            color_temp = request.POST.get('color_temp', 'RGB 16 triệu màu').strip()
            lifespan_hours = int(request.POST.get('lifespan_hours', 30000) or 30000)
            variants = request.POST.get('variants', 'Bản Tiêu Chuẩn,Bản Pro').strip()
            specs_summary = request.POST.get('specs_summary', '').strip()
            image_url = request.POST.get('image_url', '').strip()

            if prod_id:
                prod = get_object_or_404(Product, id=int(prod_id))
                prod.category = category
                prod.sku = sku
                prod.name = name
                prod.brand = brand
                prod.price = price
                prod.warranty_months = warranty_months
                prod.stock = stock
                prod.power_watt = power_watt
                prod.voltage = voltage
                prod.connectivity = connectivity
                prod.color_temp = color_temp
                prod.lifespan_hours = lifespan_hours
                prod.variants = variants
                prod.specs_summary = specs_summary
                prod.description = specs_summary
                if image_url:
                    prod.image_url = image_url
                prod.save()
                messages.success(request, f"Đã cập nhật thiết bị [{sku}] {name}.")
            else:
                prod = Product.objects.create(
                    category=category,
                    sku=sku,
                    name=name,
                    brand=brand,
                    price=price,
                    warranty_months=warranty_months,
                    stock=stock,
                    power_watt=power_watt,
                    voltage=voltage,
                    connectivity=connectivity,
                    color_temp=color_temp,
                    lifespan_hours=lifespan_hours,
                    variants=variants,
                    specs_summary=specs_summary,
                    description=specs_summary,
                    image_url=image_url,
                )
                messages.success(request, f"Đã thêm thiết bị mới [{sku}] {name}.")
            _run_async(sync_product_to_mongo, prod)

        elif action == 'delete_product':
            prod_id = int(request.POST.get('prod_id', 0))
            prod = Product.objects.filter(id=prod_id).first()
            if prod:
                sku_val = prod.sku
                prod.delete()
                if check_mongo_connection():
                    _run_async(products_col.delete_one, {'sku': sku_val})
                messages.info(request, f"Đã xóa thiết bị [{sku_val}].")

        # 3. QUẢN LÝ TÀI KHOẢN NGƯỜI DÙNG
        elif action == 'save_user':
            user_id = request.POST.get('user_id', '').strip()
            email = request.POST.get('email', '').strip().lower()
            first_name = request.POST.get('first_name', '').strip()
            password = request.POST.get('password', '').strip()
            is_staff = request.POST.get('is_staff') == 'on'
            is_active = request.POST.get('is_active') == 'on'

            if user_id:
                u = get_object_or_404(User, id=int(user_id))
                if email:
                    u.email = email
                u.first_name = first_name
                u.is_staff = is_staff
                u.is_active = is_active
                if password:
                    u.set_password(password)
                u.save()
                _run_async(sync_user_to_mongo, u)
                messages.success(request, f"Đã cập nhật tài khoản '{u.username}'.")
            elif email and password:
                if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
                    messages.warning(request, "Tài khoản Gmail này đã tồn tại.")
                else:
                    u = User.objects.create_user(
                        username=email,
                        email=email,
                        password=password,
                        first_name=first_name,
                    )
                    u.is_staff = is_staff
                    u.is_active = is_active
                    u.save()
                    _run_async(sync_user_to_mongo, u)
                    messages.success(request, f"Đã tạo tài khoản người dùng '{email}'.")

        elif action == 'delete_user':
            user_id = int(request.POST.get('user_id', 0))
            u = User.objects.filter(id=user_id).first()
            if u and u.id != request.user.id:
                uname = u.username
                u.delete()
                if check_mongo_connection():
                    _run_async(users_col.delete_one, {'username': uname})
                messages.info(request, f"Đã xóa tài khoản '{uname}'.")

        # 4. QUẢN LÝ ĐÁNH GIÁ THIẾT BỊ
        elif action == 'save_review':
            rev_id = request.POST.get('rev_id', '').strip()
            prod_id = int(request.POST.get('product_id', 0))
            prod = get_object_or_404(Product, id=prod_id)
            reviewer_name = request.POST.get('reviewer_name', 'sv.cntt@gmail.com').strip()
            rating = max(1, min(5, int(request.POST.get('rating', 5) or 5)))
            comment = request.POST.get('comment', '').strip()
            if rev_id:
                rev = get_object_or_404(Review, id=int(rev_id))
                rev.product = prod
                rev.reviewer_name = reviewer_name
                rev.rating = rating
                rev.comment = comment
                rev.save()
                messages.success(request, f"Đã cập nhật đánh giá của '{reviewer_name}'.")
            else:
                rev = Review.objects.create(
                    product=prod,
                    user=request.user,
                    reviewer_name=reviewer_name,
                    rating=rating,
                    comment=comment,
                )
                messages.success(request, f"Đã thêm đánh giá mới cho '{prod.name}'.")
            _run_async(sync_review_to_mongo, rev)

        elif action == 'delete_review':
            rev_id = int(request.POST.get('rev_id', 0))
            rev = Review.objects.filter(id=rev_id).first()
            if rev:
                rev.delete()
                if check_mongo_connection():
                    _run_async(reviews_col.delete_one, {'review_id': rev_id})
                messages.info(request, "Đã xóa đánh giá thiết bị.")

        # 5. QUẢN LÝ ĐƠN HÀNG
        elif action == 'update_order_status':
            ord_id = int(request.POST.get('order_id', 0))
            new_status = request.POST.get('status', 'pending').strip()
            ord_obj = get_object_or_404(Order, id=ord_id)
            old_status = ord_obj.status
            ord_obj.status = new_status
            ord_obj.save()

            order_items = list(ord_obj.items.select_related('product').all())
            # Nếu chuyển sang Đã hủy từ trạng thái khác, tự động hoàn lại tồn kho
            if new_status == 'cancelled' and old_status != 'cancelled':
                for item in order_items:
                    item.product.stock += item.quantity
                    item.product.save()
                _run_async(cancel_order_in_mongo, ord_obj, order_items)
            else:
                _run_async(sync_order_to_mongo, ord_obj, order_items, True)
            messages.success(request, f"Đã cập nhật trạng thái Đơn hàng #{ord_id} thành '{ord_obj.get_status_display()}'.")

        elif action == 'delete_order':
            ord_id = int(request.POST.get('order_id', 0))
            ord_obj = Order.objects.filter(id=ord_id).first()
            if ord_obj:
                ord_obj.delete()
                if check_mongo_connection():
                    _run_async(orders_col.delete_one, {'order_id': ord_id})
                messages.info(request, f"Đã xóa Đơn hàng #{ord_id}.")

        return redirect(f"/quan-ly/?tab={active_tab}")

    categories = Category.objects.all().order_by('id')
    products = Product.objects.select_related('category').all().order_by('id')
    users_list = User.objects.all().order_by('-date_joined')
    reviews_list = Review.objects.select_related('product').all().order_by('-created_at')
    orders_list = Order.objects.prefetch_related('items__product').all().order_by('-id')
    groups_list = Group.objects.all()
    recent_logs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:10]

    return render(request, 'shop/admin_panel.html', {
        'active_tab': active_tab,
        'categories': categories,
        'products': products,
        'users_list': users_list,
        'reviews_list': reviews_list,
        'orders_list': orders_list,
        'groups_list': groups_list,
        'recent_logs': recent_logs,
    })
