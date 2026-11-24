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

Lệnh kiểm tra trên Terminal:
python -c "from mongo_db import db; print(db.list_collection_names())"
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

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://vuongnguyenviethoa1111_db_user:Hoa2026cnpm@database.lj6uhtu.mongodb.net/?retryWrites=true&w=majority",
)

MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "techgear_db")

if PYMONGO_AVAILABLE:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB_NAME]

    categories_col = db["categories"]
    products_col = db["products"]
    orders_col = db["orders"]
    order_items_col = db["order_items"]
    reviews_col = db["reviews"]
    users_col = db["users"]
else:
    client = None
    db = None
    categories_col = None
    products_col = None
    orders_col = None
    order_items_col = None
    reviews_col = None
    users_col = None


def check_mongo_connection():
    """Kiểm tra kết nối thực tế tới database `techgear_db` trên MongoDB Atlas."""
    if not PYMONGO_AVAILABLE or client is None or "<db_password>" in MONGO_URI:
        return False
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
