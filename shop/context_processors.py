def cart_summary(request):
    """Context processor cung cấp số lượng món trong giỏ hàng trên thanh menu."""
    raw_cart = request.session.get('cart', {})
    total_count = sum(item.get('quantity', 0) for item in raw_cart.values())
    return {
        'cart_summary': {
            'count': total_count,
        }
    }
