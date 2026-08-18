# 🚖 NYC Taxi Analytics Dashboard - Design & Insight Guide

![NYC Taxi Executive Analytics Dashboard](https://raw.githubusercontent.com/NhatNamPhan/NYC_Taxi_Platform/master/docs/dashboard_preview.png)

Bản thiết kế chi tiết từng biểu đồ tương ứng với **8 Business Data Marts** trong dbt nhằm phục vụ xây dựng **Executive Dashboard chuẩn Business Intelligence** trên Metabase hoặc Power BI.

---

## 📌 1. Bố cục tổng thể Dashboard (Dashboard Layout Architecture)

Dashboard được thiết kế theo **Cấu trúc 4 tầng (4-Tier Layout)** từ chỉ số tổng quan đến phân tích vận hành chi tiết:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1: KEY PERFORMANCE INDICATORS (KPI SCORECARDS)                             │
│ [ Total Revenue ]     [ Total Trips ]     [ Avg Fare / Trip ]  [ Avg Tip % ]   │
├───────────────────────────────────────┬─────────────────────────────────────────┤
│ TẦNG 2: XU HƯỚNG VĨ MÔ (MACRO TRENDS) │ TẦNG 3: SO SÁNH PHÂN CÚC (SEGMENTATION) │
│ • Monthly Revenue & Trip Trend        │ • Airport vs City Trips                 │
│ • Day of Week & Weekend Performance   │ • Payment Method Breakdown              │
├───────────────────────────────────────┴─────────────────────────────────────────┤
│ TẦNG 4: PHÂN TÍCH VẬN HÀNH CHI TIẾT (OPERATIONAL DEEP-DIVE)                     │
│ • Heatmap: Hourly Demand by Borough                                             │
│ • Top 10 Revenue Pickup Zones                                                   │
│ • Top Origin-Destination Routes Matrix                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 2. Chi tiết Biểu đồ & Insight từ 8 Data Marts

### 🟢 1. `mart_kpi_summary` — Thẻ Chỉ Số KPI Tổng Quan (Instant Scorecard)
- **Loại biểu đồ**: **Number / Scorecard Cards**
- **Cấu hình**:
  - **Metrics**: `total_revenue`, `total_trips`, `avg_fare_amount`, `avg_tip_percentage`, `avg_trip_distance`
- **🎯 Business Insight mang lại**:
  - Tải tức thì (< 0.001s) các chỉ số quan trọng nhất của toàn bộ hệ thống cho cấp quản lý mà không cần query lại toàn bộ bảng Fact lớn.

---

### 🟢 2. `mart_monthly_trends` — Biến động Xu hướng theo Tháng
- **Loại biểu đồ**: **Combo Chart (Biểu đồ cột kết hợp đường - Dual Axis)**
- **Cấu hình**:
  - **Trục hoành (X-axis)**: `year-month` (Ví dụ: 2024-01, 2024-02 ... 2025-12)
  - **Cột (Bar/Column - Trục Y1)**: `total_revenue` ($)
  - **Đường (Line - Trục Y2)**: `trip_count` (Số chuyến)
- **🎯 Business Insight mang lại**:
  - **Tính mùa vụ (Seasonality)**: Nhận biết tháng có lượng đi lại cao nhất (Q4 lễ hội thường bùng nổ doanh thu).
  - **Tăng trưởng MoM (Month-over-Month)**: So sánh tốc độ phát triển giữa 2024 và 2025.

---

### 🟢 3. `mart_hourly_demand` — Nhu cầu Theo Khung Giờ & Quận
- **Loại biểu đồ**: **Heatmap (Biểu đồ nhiệt) hoặc Stacked Area Chart**
- **Cấu hình**:
  - **Trục hoành (X-axis)**: `pickup_hour` (0h đến 23h)
  - **Trục tung (Y-axis)**: `pickup_borough` (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
  - **Màu sắc (Value)**: `trip_count` hoặc `avg_speed_mph`
- **🎯 Business Insight mang lại**:
  - **Giờ cao điểm (Rush Hours)**: Đỉnh nhu cầu sáng (7h - 9h) và tối (17h - 20h).
  - **Ùn tắc giao thông**: Mật độ di chuyển ở Manhattan giờ cao điểm giảm tốc độ dưới 8-10 mph ➔ Cơ sở tính phụ phí ùn tắc (Congestion Surcharge).

---

### 🟢 4. `mart_day_of_week` — Hiệu suất Ngày Trong Tuần vs Cuối Tuần
- **Loại biểu đồ**: **Grouped Bar Chart (Biểu đồ cột nhóm)**
- **Cấu hình**:
  - **Trục X**: `day_name` (Monday ➔ Sunday)
  - **Nhóm (Legend)**: `day_type` (Weekday vs Weekend)
  - **Chỉ số**: `total_trips`, `avg_fare_amount`, `avg_tip_percentage`
- **🎯 Business Insight mang lại**:
  - **Hành vi khách hàng**: Ngày trong tuần chuyến đi ngắn hơn nhưng mật độ dày (đi làm). Cuối tuần khoảng cách trung bình (`avg_trip_distance`) dài hơn và cước cao hơn.
  - **Văn hóa Tip**: Khách đi chơi cuối tuần có xu hướng tip cao hơn (`avg_tip_percentage`).

---

### 🟢 5. `mart_revenue_by_zone` — Khu Vực "Hái Ra Tiền" (Hotspots)
- **Loại biểu đồ**: **Horizontal Bar Chart (Top 10 Zones) & Bản đồ Map (Choropleth)**
- **Cấu hình**:
  - **Trục X**: `total_revenue`
  - **Trục Y**: `pickup_zone` (Top 10)
  - **Color Tooltip**: `avg_tip_percentage`
- **🎯 Business Insight mang lại**:
  - **Top Hotspots**: Khu vực sinh lời hàng đầu (Midtown Center, Upper East Side, Financial District).
  - **Điều phối tài xế**: Hướng dẫn tài xế tập trung tại các vùng có tỷ lệ Tip cao để tối ưu thu nhập.

---

### 🟢 6. `mart_route_analysis` — Phân Tích Tuyến Đường (Origin - Destination)
- **Loại biểu đồ**: **Sankey Diagram (Luồng di chuyển) hoặc Leaderboard Table**
- **Cấu hình**:
  - **Cột**: `route_name` (Pickup Zone ➔ Dropoff Zone)
  - **Metrics**: `total_trips`, `avg_duration_min`, `avg_speed_mph`, `total_revenue`
- **🎯 Business Insight mang lại**:
  - **Tuyến đường huyết mạch**: Xác định cặp tuyến phổ biến nhất (Ví dụ: Upper East Side ➔ Midtown).
  - **Phân tích nghẽn cổ chai (Bottlenecks)**: Phát hiện tuyến có thời gian di chuyển cao nhưng tốc độ chậm (`avg_speed_mph` thấp).

---

### 🟢 7. `mart_airport_vs_city` — Chuyến Đi Sân Bay vs Nội Thành
- **Loại biểu đồ**: **Donut Chart & Side-by-Side Bar Chart**
- **Cấu hình**:
  - **Phân khúc**: `trip_type` (JFK Airport, Newark Airport, Airport Trip, City Trip)
  - **Chỉ số**: `total_revenue`, `avg_fare_amount`, `total_airport_fees`
- **🎯 Business Insight mang lại**:
  - **Biên lợi nhuận Sân Bay**: Dù số lượng chuyến chiếm < 8%, nhưng đóng góp **15-20% tổng doanh thu** nhờ cước cố định (Flat rate) và phí sân bay (`airport_fee`).

---

### 🟢 8. `mart_payment_insights` — Phương Thức Thanh Toán & Tiền Tip
- **Loại biểu đồ**: **Pie Chart & Stacked Bar Chart**
- **Cấu hình**:
  - **Phân khúc**: `payment_method` (Credit Card, Cash, No Charge, Dispute)
  - **Metrics**: `total_revenue`, `avg_tip_percentage`
- **🎯 Business Insight mang lại**:
  - **Hành vi Quẹt Thẻ**: Trên 80-85% chuyến đi thanh toán bằng Thẻ tín dụng.
  - **Insight về Tip**: Tiền tip xuất hiện chủ yếu trên các giao dịch Quẹt thẻ do gợi ý máy POS tự động.

---

## 🛠️ 3. Hướng dẫn kết nối & cài đặt trên Metabase / Power BI

### 🔹 Metabase (Đang chạy tại http://localhost:3000)
1. **Kết nối Database**:
   - Vào **Admin Settings** ➔ **Databases** ➔ **Add Database**.
   - **Database type**: PostgreSQL.
   - **Host**: `host.docker.internal` (hoặc `localhost`).
   - **Port**: `5433`.
   - **Database name**: `nyc_taxi`.
   - **Username**: `postgres` | **Password**: `1234`.
   - **Schema**: chọn `gold`.

2. **Tạo Dashboard**:
   - Tạo các Question mới từ các bảng `gold.mart_*`.
   - Tạo **Dashboard** mới và sắp xếp theo bố cục **4-Tier Layout** ở phần 1.

---

### 🔹 Power BI Desktop
1. **Lấy dữ liệu**:
   - Click **Get Data** ➔ Chọn **PostgreSQL database**.
   - **Server**: `localhost:5433` | **Database**: `nyc_taxi`.
   - Mode: **Import** (hoặc DirectQuery).
2. **Chọn Schema & Visuals**:
   - Chọn schema `gold` và tick chọn toàn bộ các bảng `mart_*`.
   - Sử dụng các hình vẽ gợi ý trong phần 2 để xây dựng visual report.
