"""Constants used throughout the application"""

# Store policies
POLICIES = {
    "shipping": """CHÍNH SÁCH VẬN CHUYỂN:
- Miễn phí vận chuyển cho đơn hàng từ 500,000đ
- Phí vận chuyển: 30,000đ cho đơn dưới 500,000đ
- Thời gian giao hàng: 
  + Nội thành: 1-2 ngày
  + Các tỉnh: 3-5 ngày làm việc
- Đóng gói cẩn thận, có thêm lớp xốp bảo vệ sản phẩm
- Khách hàng có thể theo dõi đơn hàng qua mã vận đơn""",

    "returns": """CHÍNH SÁCH ĐỔI TRẢ:
- Đổi trả miễn phí trong vòng 7 ngày kể từ ngày nhận hàng
- Điều kiện đổi trả:
  + Sản phẩm còn nguyên tem, mác, tags
  + Sản phẩm chưa qua sử dụng
  + Có đầy đủ hoá đơn mua hàng
- Các trường hợp được đổi trả:
  + Sản phẩm bị lỗi do nhà sản xuất
  + Sản phẩm không đúng mẫu mã, kích thước đã đặt
  + Sản phẩm bị hư hỏng trong quá trình vận chuyển
- Chi phí đổi trả:
  + Lỗi từ nhà sản xuất: Miễn phí
  + Lỗi từ phía khách hàng: Khách hàng chịu phí ship 2 chiều""",

    "payment": """PHƯƠNG THỨC THANH TOÁN:
- COD (Cash On Delivery): Thanh toán khi nhận hàng
- Chuyển khoản ngân hàng:
  + Vietcombank
  + Techcombank
  + MB Bank
- Ví điện tử:
  + Momo
  + ZaloPay
  + VNPay
- Thẻ tín dụng/ghi nợ qua cổng thanh toán""",

    "warranty": """CHÍNH SÁCH BẢO HÀNH:
- Thời gian bảo hành: 1-3 tháng tùy loại sản phẩm
- Phạm vi bảo hành:
  + Các lỗi về kết cấu sản phẩm
  + Các lỗi về màu sắc (bạc màu, phai màu)
  + Các lỗi về chất liệu
- Không bảo hành:
  + Sản phẩm đã qua sử dụng và bị hư hỏng do người dùng
  + Sản phẩm bị biến dạng do va đập, nhiệt độ
  + Sản phẩm hết thời hạn bảo hành""",

    "order": """QUY TRÌNH ĐẶT HÀNG:
- Bước 1: Chọn sản phẩm và thêm vào giỏ hàng
- Bước 2: Kiểm tra giỏ hàng và số lượng
- Bước 3: Điền thông tin giao hàng
- Bước 4: Chọn phương thức thanh toán
- Bước 5: Xác nhận đơn hàng
- Sau khi đặt hàng:
  + Nhận email xác nhận đơn hàng
  + Có thể theo dõi trạng thái đơn hàng
  + Nhận thông báo khi đơn hàng được giao""",

    "wholesale": """CHÍNH SÁCH BÁN SỈ:
- Số lượng tối thiểu: 10 sản phẩm/mẫu
- Chiết khấu theo số lượng:
  + 10-30 sản phẩm: Giảm 10%
  + 31-50 sản phẩm: Giảm 15%
  + Trên 50 sản phẩm: Giảm 20%
- Hỗ trợ:
  + Tư vấn chọn mẫu
  + Đóng gói theo yêu cầu
  + Hỗ trợ vận chuyển số lượng lớn""",

    "custom": """DỊCH VỤ THEO YÊU CẦU:
- Nhận đặt hàng theo mẫu riêng
- Thời gian thực hiện: 7-15 ngày tùy độ phức tạp
- Quy trình:
  + Tư vấn và báo giá
  + Gửi bản phác thảo
  + Thực hiện sau khi khách đồng ý
  + Gửi ảnh sản phẩm trước khi giao
- Đặt cọc 50% giá trị đơn hàng""",
}

# Product categories
CATEGORIES = [
    "Nón",
    "Giỏ",
    "Đồ Gia Dụng",
    "Tranh",
    "Tượng"
]

# Materials
MATERIALS = [
    "Lá cọ",
    "Tre",
    "Gỗ",
    "Vải",
    "Mây",
    "Đá"
]

# Order statuses
ORDER_STATUSES = [
    "Đang xử lý",
    "Đã xác nhận",
    "Đang giao hàng",
    "Đã giao",
    "Đã hủy"
] 