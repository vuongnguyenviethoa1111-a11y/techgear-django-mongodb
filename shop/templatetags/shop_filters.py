from django import template

register = template.Library()


@register.filter(name='vnd')
def vnd_format(value):
    """Định dạng số nguyên thành dấu chấm phân cách hàng nghìn (ví dụ: 950.400)."""
    try:
        num = int(float(value or 0))
        return f"{num:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
