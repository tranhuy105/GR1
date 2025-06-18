# Chatbot Hỗ Trợ Cửa Hàng Thủ Công Mỹ Nghệ

## Mô tả dự án
Dự án là một **chatbot hỗ trợ khách hàng** cho cửa hàng bán sản phẩm thủ công mỹ nghệ Việt Nam, được phát triển như một bài tập môn học. Chatbot giúp khách hàng tương tác dễ dàng với cửa hàng thông qua các tính năng chính:
- **Tìm kiếm sản phẩm**: Tìm sản phẩm theo danh mục (Nón, Giỏ, Đồ Gia Dụng, Tranh, Tượng), chất liệu, giá cả, hoặc từ khóa mô tả, sử dụng tìm kiếm ngữ nghĩa kết hợp từ khóa.
- **Quản lý giỏ hàng và đơn hàng**: Thêm/xóa/cập nhật sản phẩm trong giỏ hàng, đặt hàng, xem lịch sử đơn hàng, hoặc hủy đơn hàng.
- **Tra cứu chính sách**: Cung cấp thông tin về vận chuyển, đổi trả, thanh toán, bảo hành, bán sỉ, và dịch vụ tùy chỉnh.
- **Thông tin văn hóa**: Cung cấp chi tiết về nguồn gốc, kỹ thuật chế tác, và ý nghĩa văn hóa của sản phẩm, giúp nâng cao giá trị sản phẩm thủ công Việt Nam.
- **Xác nhận hành động nhạy cảm**: Yêu cầu phê duyệt cho các hành động như thêm sản phẩm vào giỏ, đặt hàng, hoặc hủy đơn để đảm bảo an toàn.

## Mục tiêu
Xây dựng một chatbot thông minh, thân thiện, hỗ trợ khách hàng mua sắm sản phẩm thủ công mỹ nghệ, đồng thời quảng bá giá trị văn hóa Việt Nam qua thông tin chi tiết về sản phẩm.

## Công nghệ sử dụng
- **Ngôn ngữ lập trình**: Python
- **Backend**: FastAPI để xây dựng API RESTful cho chatbot.
- **Cơ sở dữ liệu**: SQLite để lưu trữ thông tin sản phẩm, đơn hàng, và giỏ hàng.
- **Xử lý ngôn ngữ tự nhiên**: LangChain và LangGraph để quản lý luồng hội thoại và gọi công cụ.
- **Tìm kiếm thông minh**: Sử dụng FAISS (vector store) và TF-IDF cho tìm kiếm hybrid (ngữ nghĩa + từ khóa), tích hợp Google Generative AI Embeddings.
- **Môi trường**: Sử dụng `.env` để quản lý các biến môi trường như đường dẫn cơ sở dữ liệu và API key.

## Cấu trúc dự án
- **constants.py**: Chứa các hằng số như danh mục sản phẩm, chất liệu, trạng thái đơn hàng, và chính sách cửa hàng.
- **db.py**: Xử lý các thao tác SQL (tìm kiếm sản phẩm, quản lý giỏ hàng, đơn hàng).
- **db_setup.py**: Khởi tạo cơ sở dữ liệu với dữ liệu mẫu (50+ sản phẩm thủ công).
- **rag_search.py / rag_tools.py**: Xử lý tìm kiếm ngữ nghĩa, thông tin văn hóa, và sản phẩm tương tự.
- **enhanced_chatbot.py / agent.py / tools.py**: Xây dựng logic chatbot, xử lý các công cụ (tools) như thêm vào giỏ hàng, tra cứu chính sách, và tìm kiếm sản phẩm.
- **api.py**: Cung cấp API để giao tiếp với chatbot qua giao diện web.
- **utils.py**: Các hàm tiện ích hỗ trợ xử lý lỗi công cụ và in trạng thái hội thoại.

## Các tính năng nổi bật
- **Tìm kiếm thông minh**: Kết hợp tìm kiếm ngữ nghĩa (dựa trên ý nghĩa câu hỏi) và từ khóa để trả về kết quả chính xác. Ví dụ: "Tìm quà tặng cho người nước ngoài" sẽ trả về sản phẩm phù hợp như nón lá mini.
- **Quản lý giao dịch an toàn**: Các hành động như thêm sản phẩm vào giỏ, đặt hàng, hoặc hủy đơn yêu cầu xác nhận từ người dùng để tránh sai sót.
- **Thông tin văn hóa chi tiết**: Mỗi sản phẩm đi kèm mô tả về nguồn gốc, kỹ thuật chế tác, và ý nghĩa văn hóa, giúp khách hàng hiểu rõ giá trị thủ công Việt Nam.
- **Gợi ý tiếp theo**: Sau mỗi phản hồi, chatbot cung cấp 2-4 gợi ý (selections) để khuyến khích khách hàng tiếp tục mua sắm hoặc tìm hiểu thêm.

## Cách chạy dự án
1. **Cài đặt môi trường**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Cấu hình biến môi trường**:
 Tạo file `.env` với các biến:
    ```
    DB_PATH=data/handicraft.sqlite
    GOOGLE_API_KEY=<your-google-api-key>
    PORT=8000
    ```
3. **Khởi tạo cơ sở dữ liệu**:
   ```bash
   python db_setup.py
   ```
4. **Chạy API**:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```
5. **Truy cập giao diện**:
   - Mở trình duyệt tại `http://localhost:8000` để sử dụng chatbot qua giao diện web.

## Ví dụ sử dụng
- **Tìm kiếm sản phẩm**: "Tôi muốn tìm nón lá giá dưới 200,000đ" → Chatbot trả về danh sách nón lá phù hợp, kèm gợi ý thêm vào giỏ hàng.
- **Xem giỏ hàng**: "Giỏ hàng của tôi có gì?" → Chatbot hiển thị danh sách sản phẩm, số lượng, và tổng tiền.
- **Tra cứu chính sách**: "Chính sách đổi trả là gì?" → Chatbot trả về thông tin chính sách đổi trả.
- **Đặt hàng**: "Thêm 2 nón lá ID 1 vào giỏ và đặt hàng" → Chatbot yêu cầu xác nhận, sau đó tạo đơn hàng.

## Kết quả đạt được
- Chatbot xử lý tốt các yêu cầu của khách hàng, từ tìm kiếm sản phẩm đến quản lý đơn hàng.
- Tích hợp thành công tìm kiếm ngữ nghĩa và từ khóa, nâng cao trải nghiệm người dùng.
- Cung cấp thông tin văn hóa phong phú, giúp quảng bá giá trị thủ công Việt Nam.
- Đảm bảo an toàn giao dịch với cơ chế xác nhận hành động nhạy cảm.
