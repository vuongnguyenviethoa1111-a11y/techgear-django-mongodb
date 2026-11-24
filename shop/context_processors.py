from .mongo_client import load_user_cart_from_mongo


def cart_summary(request):
    """
    Context processor cung cấp số lượng món trong giỏ hàng trên thanh menu.
    Nếu khách đã đăng nhập mà session giỏ hàng đang trống (ví dụ vừa đăng nhập lại),
    tự động khôi phục giỏ hàng đã lưu từ collection `users` trên MongoDB Atlas.
    """
    raw_cart = request.session.get('cart', {})
    if request.user.is_authenticated and not raw_cart:
        saved_cart, saved_promo = load_user_cart_from_mongo(request.user)
        if saved_cart:
            raw_cart = saved_cart
            request.session['cart'] = raw_cart
            if saved_promo and not request.session.get('promo_code'):
                request.session['promo_code'] = saved_promo
            request.session.modified = True

    total_count = sum(item.get('quantity', 0) for item in raw_cart.values())
    return {
        'cart_summary': {
            'count': total_count,
        }
    }
