# NỘI DUNG THAM KHẢO VIẾT BÁO CÁO ĐỒ ÁN: WEBSITE PHỤ KIỆN CÔNG NGHỆ, ĐÈN LED & THIẾT BỊ THÔNG MINH (DJANGO + MONGODB)

Tài liệu này được tổng hợp sát 100% với mã nguồn thực tế trong dự án **`TechGear LED & Smart Devices`** để bạn copy trực tiếp vào file Word/Slide báo cáo đồ án môn học.

---

## 1. Giới thiệu đề tài & Lý do chọn đề tài
- **Tên đề tài:** Xây dựng Website kinh doanh và quản lý Phụ kiện công nghệ, Đèn LED & Thiết bị thông minh (**TechGear LED & Smart Devices**) sử dụng Django Framework kết hợp MongoDB Atlas.
- **Link triển khai thực tế (Railway Cloud - Port 8080):** https://techgear-django-mongodb-production.up.railway.app/
- **Lý do chọn đề tài:**
  - Các mặt hàng công nghệ, đèn LED thông minh và thiết bị Smart Home có nhiều **thông số kỹ thuật đặc thù** (Mã SKU, Công suất tiêu thụ Watt, Điện áp hoạt động, Chuẩn kết nối Wi-Fi/Bluetooth/USB-C, Nhiệt độ màu Kelvin/RGB, Tuổi thọ giờ chiếu sáng) và yêu cầu quản lý **thời hạn bảo hành điện tử (12–24 tháng)** cùng **tồn kho thực tế**.
  - Kết hợp kiến trúc **MVT (Model – View – Template)** của Django với mô hình dữ liệu **Document/Collection của MongoDB (qua PyMongo)** giúp lưu trữ linh hoạt các thông số kỹ thuật dạng sub-document JSON mà vẫn tận dụng được hệ thống xác thực, phân quyền Admin và quản lý Session mạnh mẽ của Django.

---

## 2. Kiến trúc hệ thống (Django MVT + PyMongo)

1. **Tầng Giao diện (Template - HTML5/CSS3/JS theo chuẩn MDN Web Docs):**
   - Giao diện kế thừa từ `shop/templates/shop/base.html`, phân tách rõ các trang:
     - `home.html`: Trang chủ, bộ lọc danh mục, tìm kiếm theo thông số kỹ thuật và **Công cụ tính công suất đèn LED theo diện tích phòng ($m^2$)**.
     - `product_detail.html`: Trang bảng thông số kỹ thuật chi tiết, chính sách bảo hành và gửi đánh giá (`reviews`).
     - `cart.html` & `checkout.html`: Giỏ hàng lưu qua Django `Session`, kiểm tra tồn kho (`stock`), áp mã giảm giá (`TECH20`, `SMART10`) và chọn phương thức thanh toán (`COD` / `QR Banking`).
     - `warranty_check.html`: Trang tra cứu bảo hành điện tử theo Số điện thoại hoặc Mã đơn hàng.
     - `dashboard.html`: Trang thống kê tổng tồn kho, cảnh báo thiết bị sắp hết hàng (`stock <= 10`), doanh thu và trạng thái kết nối 6 collections MongoDB.

2. **Tầng Xử lý nghiệp vụ (View & URL Routing - `shop/views.py`, `shop/urls.py`):**
   - Nhận HTTP Request từ người dùng, truy vấn và kiểm tra ràng buộc dữ liệu (chặn đặt vượt quá `stock`, tự động trừ `stock` khi đặt hàng và hoàn trả `stock` khi khách hủy đơn ở trạng thái `pending`).

3. **Tầng Dữ liệu & Kết nối MongoDB Atlas (`mongo_db.py` & `shop/views.py`):**
   - File `mongo_db.py` (đặt cùng cấp với `manage.py`) sử dụng `MongoClient` của thư viện **PyMongo** kết nối tới `MONGO_URI` (MongoDB Atlas) trên database **`techgear_db`** và khởi tạo sẵn đúng **6 Collections**:
     - `categories_col = db["categories"]`: Lưu phân loại danh mục thiết bị.
     - `products_col = db["products"]`: Lưu thông tin thiết bị, `sku`, `brand`, `price`, `warranty_months`, `stock` và thông số kỹ thuật (`power_watt`, `voltage`, `connectivity`, `color_temp`, `lifespan_hours`).
     - `orders_col = db["orders"]`: Lưu thông tin đơn hàng và SĐT kích hoạt bảo hành điện tử (`user_id`, `full_name`, `phone`, `address`, `total_price`, `status`, `created_at`).
     - `order_items_col = db["order_items"]`: Lưu từng dòng thiết bị trong đơn (`order_id`, `product_id`, `quantity`, `price`).
     - `reviews_col = db["reviews"]`: Lưu đánh giá kỹ thuật của khách hàng (`product_id`, `reviewer_name`, `rating`, `comment`).
     - `users_col = db["users"]`: Lưu thông tin tài khoản Gmail khách hàng và quản trị viên (`user_id`, `username`, `email`, `is_staff`).
   - Kiểm tra nhanh kết nối từ Terminal:
     ```bash
     python -c "from mongo_db import db; print(db.list_collection_names())"
     ```

---

## 3. Tài liệu tham khảo (Chuẩn trích dẫn để đưa vào cuối Báo cáo)

1. **Django Software Foundation.** *Django Documentation (Web framework for perfectionists with deadlines)* — Hướng dẫn về MVT (Model–View–Template), ORM, URL routing, Session, Form và Django Admin. Truy cập tại: https://docs.djangoproject.com/
2. **MongoDB, Inc.** *MongoDB Manual & MongoDB Atlas Documentation* — Tài liệu về mô hình dữ liệu Document/Collection, tạo database/collection trên MongoDB Atlas và truy vấn dữ liệu. Truy cập tại: https://www.mongodb.com/docs/
3. **MongoDB PyMongo Team.** *PyMongo Documentation* — Hướng dẫn kết nối Python với MongoDB (`MongoClient`), thao tác đọc/ghi dữ liệu trên các collection (`categories`, `products`, `orders`, `order_items`, `reviews`, `users`). Truy cập tại: https://pymongo.readthedocs.io/
4. **MDN Web Docs (Mozilla).** *HTML, CSS, and JavaScript Guides* — Tài liệu chuẩn về cấu trúc HTML5, định dạng CSS layout/responsive và xử lý sự kiện phía client. Truy cập tại: https://developer.mozilla.org/
5. **Giáo trình / Slide bài giảng môn học Lập trình Web / Phát triển ứng dụng Web** — Khoa Công nghệ Thông tin (Điền thêm tên giảng viên hướng dẫn và tên trường của bạn).
