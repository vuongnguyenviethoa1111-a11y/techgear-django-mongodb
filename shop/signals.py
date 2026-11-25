"""
Django Signals: Tự động đồng bộ dữ liệu sang MongoDB (`techgear_db`)
mỗi khi Admin hoặc người dùng thêm/sửa dữ liệu trên 6 collections:
`categories`, `products`, `orders`, `order_items`, `reviews`, `users`.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Product, Order, OrderItem, Review
from .mongo_client import (
    _run_async,
    sync_category_to_mongo,
    sync_product_to_mongo,
    sync_order_to_mongo,
    sync_review_to_mongo,
    sync_user_to_mongo,
)


@receiver(post_save, sender=Category)
def on_category_save(sender, instance, **kwargs):
    _run_async(sync_category_to_mongo, instance)


@receiver(post_save, sender=Product)
def on_product_save(sender, instance, **kwargs):
    _run_async(sync_product_to_mongo, instance)


@receiver(post_save, sender=Order)
def on_order_save(sender, instance, **kwargs):
    items = list(instance.items.select_related('product').all())
    _run_async(sync_order_to_mongo, instance, items)


@receiver(post_save, sender=OrderItem)
def on_order_item_save(sender, instance, **kwargs):
    order = instance.order
    items = list(order.items.select_related('product').all())
    _run_async(sync_order_to_mongo, order, items)


@receiver(post_save, sender=Review)
def on_review_save(sender, instance, **kwargs):
    _run_async(sync_review_to_mongo, instance)


@receiver(post_save, sender=User)
def on_user_save(sender, instance, **kwargs):
    _run_async(sync_user_to_mongo, instance)
