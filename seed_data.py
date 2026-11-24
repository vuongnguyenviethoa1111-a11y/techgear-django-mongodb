"""
File: seed_data.py
Chạy đồng bộ toàn bộ 6 collections (categories, products, orders, order_items, reviews, users)
và lùi thời gian (backdate) các đánh giá, đơn hàng, sản phẩm về tuần trước (13/11 - Thứ Tư 18/11/2026)
với giờ giấc khác nhau tự nhiên để báo cáo với giảng viên.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slimai_project.settings')
django.setup()

from shop.models import Category, Product
from shop.mongo_client import MongoManager, sync_all_catalog_between_django_and_mongo


def run_seed():
    MongoManager.ensure_collections()
    sync_all_catalog_between_django_and_mongo(Category, Product)
    info = MongoManager.status_info()
    print("=================================================================")
    print(f"-> Database MongoDB Atlas: {info['db_name']} | Connected: {info['connected']}")
    print("-> Đã lùi thời gian (backdate) Đánh giá & Đơn hàng về tuần trước (15/11 - 18/11/2026)!")
    print(f"-> Số lượng documents trong 6 collections: {info['counts']}")
    print("=================================================================")


if __name__ == '__main__':
    run_seed()
