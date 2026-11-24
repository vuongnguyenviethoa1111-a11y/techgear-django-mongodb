"""
File: mongo_db.py (Đặt cùng cấp với manage.py)
Kết nối trực tiếp dự án Django TechGear với MongoDB Atlas trên database `techgear_db`
và cung cấp đúng 6 collections:
- categories_col  -> db["categories"]
- products_col    -> db["products"]
- orders_col      -> db["orders"]
- order_items_col -> db["order_items"]
- reviews_col     -> db["reviews"]
- users_col       -> db["users"]
"""
import os

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from bson import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    MongoClient = None
    ObjectId = str
    ASCENDING = 1
    DESCENDING = -1
    PYMONGO_AVAILABLE = False

DEFAULT_ATLAS_URI = (
    "mongodb+srv://vuongnguyenviethoa1111_db_user:Hoa2026cnpm@database.lj6uhtu.mongodb.net/?retryWrites=true&w=majority"
)

_env_uri = (os.environ.get("MONGO_URI") or "").strip()
# Bảo vệ trường hợp biến MONGO_URI trên Railway bị điền nhầm thành username thay vì mongodb+srv://
if _env_uri.startswith("mongodb://") or _env_uri.startswith("mongodb+srv://"):
    MONGO_URI = _env_uri
else:
    MONGO_URI = DEFAULT_ATLAS_URI

MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "techgear_db")

client = None
db = None
categories_col = None
products_col = None
orders_col = None
order_items_col = None
reviews_col = None
users_col = None

if PYMONGO_AVAILABLE:
    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=2500,
            connectTimeoutMS=2500,
            socketTimeoutMS=3000,
        )
        db = client[MONGO_DB_NAME]

        categories_col = db["categories"]
        products_col = db["products"]
        orders_col = db["orders"]
        order_items_col = db["order_items"]
        reviews_col = db["reviews"]
        users_col = db["users"]
    except Exception:
        client = None
        db = None


def check_mongo_connection():
    """Kiểm tra kết nối thực tế tới database `techgear_db` trên MongoDB Atlas."""
    if not PYMONGO_AVAILABLE or client is None or db is None:
        return False
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
