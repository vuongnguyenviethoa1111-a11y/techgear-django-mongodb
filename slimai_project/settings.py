from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-techgear-led-smartdevice-mongodb-2026'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    "techgear-django-mongodb-production.up.railway.app",
    ".up.railway.app",
    "localhost",
    "127.0.0.1",
    "*",
]

CSRF_TRUSTED_ORIGINS = [
    "https://techgear-django-mongodb-production.up.railway.app",
    "https://*.up.railway.app",
    "https://*.railway.app",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'slimai_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'shop' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.cart_summary',
            ],
        },
    },
]

WSGI_APPLICATION = 'slimai_project.wsgi.application'

# 1. Cấu hình Django ORM Database (Phục vụ Session, Auth, Admin)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'TechGearDB.sqlite3',
    }
}

# ==============================================================================
# 2. CẤU HÌNH KẾT NỐI MONGODB ATLAS / LOCAL QUA PYMONGO (MongoClient)
# - Tên database bắt buộc: techgear_db
# - 6 collections chuẩn: categories, products, orders, order_items, reviews, users
# ==============================================================================
MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb+srv://vuongnguyenviethoa1111_db_user:Hoa2026cnpm@database.lj6uhtu.mongodb.net/?retryWrites=true&w=majority'
)
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'techgear_db')

LANGUAGE_CODE = 'vi'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
WHITENOISE_USE_FINDERS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
