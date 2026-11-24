from django.shortcuts import render
from django.http import JsonResponse


def home(request):
    """Render trang chủ SlimAI Liquid Glass (sử dụng trực tiếp index.html)."""
    return render(request, 'index.html')


def ai_size_api(request):
    """API phụ trợ tính size AI nếu gọi từ client qua Django."""
    try:
        height = float(request.GET.get('height', 168))
        weight = float(request.GET.get('weight', 62))
        pref = request.GET.get('pref', 'regular')
    except ValueError:
        return JsonResponse({'error': 'Chiều cao hoặc cân nặng không hợp lệ'}, status=400)

    bmi = round(weight / ((height / 100) ** 2), 1)
    if weight <= 55 and height <= 165:
        idx = 0
    elif weight <= 66 and height <= 173:
        idx = 1
    elif weight <= 76 and height <= 180:
        idx = 2
    else:
        idx = 3

    if pref == 'slim' and bmi < 23.5:
        idx = max(0, idx - 1)
    elif pref == 'relaxed':
        idx = min(3, idx + 1)

    sizes = ['S', 'M', 'L', 'XL']
    return JsonResponse({
        'recommended_size': sizes[idx],
        'bmi': bmi,
        'height': height,
        'weight': weight,
        'pref': pref,
    })
