import os
import sqlite3
import getpass
from datetime import datetime
from dotenv import load_dotenv

from constants import CATEGORIES, MATERIALS, ORDER_STATUSES

load_dotenv()

def create_schema(conn):
    """Create database schema for products, orders, order_items, carts, and cart_items."""
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        material TEXT,
        price DECIMAL,
        stock_quantity INTEGER,
        description TEXT,
        origin_location TEXT,
        crafting_technique TEXT,
        cultural_significance TEXT,
        dimensions TEXT,
        care_instructions TEXT,
        tags TEXT
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        customer_id TEXT,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        total_amount DECIMAL
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price_at_time DECIMAL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE IF NOT EXISTS carts (
        cart_id INTEGER PRIMARY KEY,
        customer_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cart_items (
        cart_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price_at_time DECIMAL,
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)
    conn.commit()

def generate_products():
    """Generate rich, detailed Vietnamese handicraft products with cultural context."""
    products = [
        # NÓN CATEGORY
        (1, "Nón Lá Cổ Điển Huế", "Nón", "Lá cọ", 120000, 45, 
         "Nón lá truyền thống từ làng nghề Chuông, Thanh Oai, Hà Nội với lịch sử hơn 300 năm. Được làm từ lá cọ non, khô tự nhiên dưới nắng, tạo màu vàng đặc trưng. Mỗi chiếc nón được đan bằng tay qua 15 công đoạn tỉ mỉ. Không chỉ che nắng che mưa hiệu quả, nón lá còn là biểu tượng của người phụ nữ Việt Nam thôn dã, dịu dàng.",
         "Làng Chuông, Thanh Oai, Hà Nội", "Đan lá cọ thủ công truyền thống", 
         "Biểu tượng của phụ nữ Việt Nam, thường xuất hiện trong thơ ca, hội họa", 
         "Đường kính 40-42cm, chiều cao 15cm", 
         "Tránh ẩm ướt, phơi nắng nhẹ khi cần thiết, bảo quản nơi khô ráo",
         "nón lá, truyền thống, Huế, che nắng, quà tặng, văn hóa Việt"),
        
        (2, "Nón Lá Thêu Thơ Huế", "Nón", "Lá cọ", 350000, 25,
         "Nón lá đặc biệt của Huế với những câu thơ được thêu tinh xảo bằng chỉ tơ tằm trên mặt nón. Khi đội nón và nhìn lên trời, ánh sáng xuyên qua sẽ hiện ra những vần thơ du dương về tình yêu, quê hương. Nghệ thuật thêu chữ trên nón lá là di sản văn hóa phi vật thể của Việt Nam, thể hiện tài hoa và sự tinh tế của người thợ Huế.",
         "Kinh đô Huế, Thừa Thiên Huế", "Thêu chỉ tơ tằm trên lá cọ", 
         "Di sản văn hóa phi vật thể, nghệ thuật thêu truyền thống Huế", 
         "Đường kính 42cm, các câu thơ dài 3-7 từ mỗi câu", 
         "Không giặt nước, lau nhẹ bằng khăn mềm, tránh ánh sáng mạnh",
         "nón lá, Huế, thêu thơ, di sản, cao cấp, văn học, tơ tằm"),

        (3, "Nón Bài Thơ Nguyễn Du", "Nón", "Lá cọ", 280000, 20,
         "Nón lá đặc biệt được thêu những câu thơ nổi tiếng của Nguyễn Du, đặc biệt là trích đoạn từ Truyện Kiều. Được các nghệ nhân lành nghề ở Huế thực hiện, mỗi chiếc nón là một tác phẩm nghệ thuật độc đáo. Thích hợp làm quà tặng cho những người yêu văn học hoặc sưu tập đồ lưu niệm văn hóa Việt Nam.",
         "Kinh đô Huế, Thừa Thiên Huế", "Thêu thơ truyền thống", 
         "Tôn vinh di sản văn học Việt Nam, đại thi hào Nguyễn Du", 
         "Đường kính 41cm, thơ được thêu bằng chỉ vàng", 
         "Bảo quản cẩn thận, tránh va đập, để nơi thoáng mát",
         "nón lá, Nguyễn Du, Truyện Kiều, văn học, quà tặng, cao cấp"),

        (4, "Nón Lá Mini Trang Trí", "Nón", "Lá cọ", 45000, 100,
         "Nón lá thu nhỏ dùng để trang trí nhà cửa, bàn làm việc hoặc làm quà lưu niệm. Mặc dù nhỏ gọn nhưng vẫn được làm theo đúng quy trình truyền thống. Thường được treo thành cụm hoặc đặt trên kệ trang trí. Rất phù hợp cho khách du lịch nước ngoài mua về làm quà hoặc trang trí không gian theo phong cách Việt Nam.",
         "Đồng bằng Bắc Bộ", "Đan thủ công thu nhỏ", 
         "Lưu niệm, trang trí, giới thiệu văn hóa Việt Nam", 
         "Đường kính 15-20cm, nhiều kích cỡ khác nhau", 
         "Dễ bảo quản, lau chùi bằng khăn khô",
         "nón lá, mini, trang trí, lưu niệm, du lịch, quà tặng"),

        (5, "Nón Lá Cô Ba Sài Gòn", "Nón", "Lá cọ", 95000, 60,
         "Nón lá với kiểu dáng đặc trưng của miền Nam, vành nón rộng hơn, tạo độ che rộng tốt hưn cho khí hậu nắng nóng. Thường được các cô gái Sài Gòn xưa đội khi đi chợ hoặc dạo phố. Màu sắc tươi sáng hơn so với nón lá miền Bắc, phản ánh sự năng động của miền Nam. Là phụ kiện không thể thiếu trong trang phục áo dài truyền thống.",
         "Sài Gòn, TP.HCM", "Đan lá cọ miền Nam", 
         "Đặc trưng văn hóa miền Nam, thời kỳ Sài Gòn xưa", 
         "Đường kính 44-45cm, vành rộng", 
         "Bảo quản nơi khô ráo, tránh ẩm mốc",
         "nón lá, Sài Gòn, miền Nam, áo dài, truyền thống, cổ điển"),

        # GIỎ CATEGORY  
        (6, "Giỏ Đan Mây Tròn Cổ Điển", "Giỏ", "Mây", 180000, 35,
         "Giỏ đan từ mây tự nhiên theo công nghệ truyền thống của làng nghề Phú Vinh, An Giang. Sản phẩm có độ bền cao, thấm hút ẩm tốt, thích hợp đựng bánh kẹo, trái cây hoặc làm giỏ quà tặng. Màu mây tự nhiên tạo cảm giác gần gũi, ấm cúng. Mỗi sợi mây được chọn lọc kỹ càng, đan chặt chẽ tạo độ chắc chắn cao.",
         "Làng Phú Vinh, An Giang", "Đan mây truyền thống", 
         "Nghề thủ công truyền thống miền Tây Nam Bộ", 
         "Đường kính 25cm, cao 15cm, có quai xách", 
         "Rửa nước nhẹ, phơi khô tự nhiên, tránh ngâm lâu",
         "giỏ mây, đan thủ công, miền Tây, tự nhiên, thân thiện môi trường"),

        (7, "Giỏ Tre Đan Vuông", "Giỏ", "Tre", 220000, 28,
         "Giỏ tre hình vuông được đan từ tre già, cắt thành nan mỏng và đan theo kỹ thuật truyền thống của làng Phụ Dực, Hà Nội. Tre được xử lý kỹ càng để chống mọt, chống ẩm. Giỏ có thể dùng để đựng đồ gia dụng, sách vở, hoặc trang trí. Màu vàng tự nhiên của tre tạo vẻ đẹp mộc mạc, phù hợp với không gian sống hiện đại.",
         "Làng Phụ Dực, Hà Nội", "Đan tre truyền thống", 
         "Nghề làm đồ tre nứa truyền thống Bắc Bộ", 
         "Kích thước 30x30x20cm, form vuông vửa", 
         "Lau khô sau khi dùng, bảo quản nơi thoáng mát",
         "giỏ tre, vuông, Hà Nội, truyền thống, tự nhiên, bền đẹp"),

        (8, "Giỏ Lục Bình Oval", "Giỏ", "Lục bình", 160000, 42,
         "Giỏ đan từ cây lục bình khô, một loại thực vật thủy sinh phổ biến ở đồng bằng sông Cửu Long. Sau khi thu hoạch, lục bình được phơi khô và đan thành giỏ. Đây là sản phẩm thân thiện với môi trường, vừa tận dụng được cây lục bình - loại cây thường bị coi là cỏ dại, vừa tạo ra sản phẩm hữu ích. Giỏ có màu nâu tự nhiên, kết cấu chắc chắn.",
         "Đồng bằng sông Cửu Long", "Đan lục bình khô", 
         "Tái chế thực vật, bảo vệ môi trường, tận dụng tài nguyên", 
         "Hình oval 35x25cm, cao 18cm", 
         "Tránh ẩm ướt, để nơi khô ráo, thông thoáng",
         "giỏ lục bình, thân thiện môi trường, miền Tây, oval, tái chế"),

        (9, "Giỏ Cói Đan Hoa Văn", "Giỏ", "Cói", 145000, 50,
         "Giỏ đan từ cói với họa tiết hoa văn truyền thống Việt Nam. Cói được trồng và thu hoạch ở vùng đất phù sa ven sông, có sợi dai, mềm mại. Kỹ thuật đan tạo ra những họa tiết hình học đẹp mắt, thể hiện tính thẩm mỹ cao của người thợ thủ công Việt Nam. Giỏ thích hợp đựng đồ khô, trang trí hoặc làm quà tặng.",
         "Vùng đồng bằng Bắc Bộ", "Đan cói với họa tiết", 
         "Nghệ thuật đan cói truyền thống, họa tiết dân gian", 
         "Đường kính 28cm, cao 16cm, có nắp đậy", 
         "Giữ khô ráo, tránh ánh nắng trực tiếp",
         "giỏ cói, hoa văn, truyền thống, nghệ thuật, đan thủ công"),

        (10, "Giỏ Quà Tết Sang Trọng", "Giỏ", "Mây", 450000, 15,
         "Giỏ quà Tết được thiết kế đặc biệt với màu đỏ may mắn và họa tiết chữ Phúc, chữ Lộc. Được làm từ mây cao cấp, tỉ mỉ trong từng chi tiết. Bên trong lót vải đỏ mềm mại, có ngăn chia để đựng các loại bánh kẹo, mứt Tết. Nắp giỏ có thể đóng mở, trang trí hoa mai vàng hoặc hoa đào hồng. Là lựa chọn tuyệt vời để biếu tặng trong dịp Tết Nguyên Đán.",
         "Làng nghề truyền thống Việt Nam", "Đan mây cao cấp, trang trí thủ công", 
         "Biểu tượng may mắn, thịnh vượng trong văn hóa Tết Việt Nam", 
         "Kích thước lớn 40x30x25cm, có quai xách", 
         "Bảo quản cẩn thận, có thể tái sử dụng nhiều năm",
         "giỏ quà, Tết, may mắn, sang trọng, mây cao cấp, phúc lộc"),

        # ĐỒ GIA DỤNG CATEGORY
        (11, "Khay Gỗ Mun Truyền Thống", "Đồ Gia Dụng", "Gỗ", 380000, 22,
         "Khay gỗ mun được chế tác từ gỗ mun quý hiếm, có màu đen bóng tự nhiên và vân gỗ đẹp. Gỗ mun được biết đến với độ cứng cao, chống mối mọt tốt và có hương thơm nhẹ đặc trưng. Khay được đánh bóng thủ công, bề mặt láng mịn. Thích hợp dùng để trà nước, đựng bánh kẹo trong các dịp lễ tết hoặc tiếp khách quan trọng.",
         "Miền núi Bắc Bộ", "Chạm khắc gỗ mun thủ công", 
         "Gỗ quý trong văn hóa Việt Nam, biểu tượng phú quý", 
         "Kích thước 45x30x3cm, bề mặt phẳng, không cong vênh", 
         "Lau sạch sau khi dùng, thoa dầu dưỡng gỗ định kỳ",
         "khay gỗ, mun, cao cấp, truyền thống, trà nước, tiếp khách"),

        (12, "Hộp Đựng Trà Gỗ Hương", "Đồ Gia Dụng", "Gỗ", 290000, 30,
         "Hộp đựng trà được làm từ gỗ hương thơm tự nhiên, có tác dụng giữ hương vị trà và chống ẩm hiệu quả. Bên trong được chia thành nhiều ngăn nhỏ để đựng các loại trà khác nhau. Nắp hộp khắc hình rồng phượng hoặc hoa sen, thể hiện nét đẹp truyền thống Việt Nam. Sản phẩm thích hợp cho những người yêu thích văn hóa trà Việt Nam.",
         "Vùng núi Quảng Nam", "Chạm khắc gỗ hương thủ công", 
         "Văn hóa trà Việt Nam, nghệ thuật chạm khắc truyền thống", 
         "Kích thước 25x18x8cm, có 6 ngăn chia", 
         "Để nơi khô ráo, thoáng mát, không đậy kín quá lâu",
         "hộp trà, gỗ hương, chạm khắc, văn hóa trà, thơm tự nhiên"),

        (13, "Bát Gỗ Dừa Tự Nhiên", "Đồ Gia Dụng", "Gỗ", 85000, 80,
         "Bát được làm từ vỏ dừa tự nhiên, qua quá trình chà nhám và đánh bóng tỉ mỉ. Vỏ dừa có tính kháng khuẩn tự nhiên, không độc hại, an toàn cho sức khỏe. Bát có màu nâu tự nhiên với vân gỗ dừa đẹp mắt, mang lại cảm giác mộc mạc, gần gũi. Thích hợp đựng cơm, canh, hoặc làm bát trang trí.",
         "Miền Tây Nam Bộ, vùng trồng dừa", "Gia công vỏ dừa thủ công", 
         "Tái chế vỏ dừa, thân thiện môi trường, zero waste", 
         "Đường kính 12cm, sâu 6cm, vừa tay cầm", 
         "Rửa nước thường, không ngâm lâu, phơi khô sau khi dùng",
         "bát dừa, tự nhiên, thân thiện môi trường, tái chế, an toàn"),

        (14, "Thớt Gỗ Cẩm Lai Oval", "Đồ Gia Dụng", "Gỗ", 320000, 25,
         "Thớt gỗ cẩm lai với hình dạng oval thanh lịch, được làm từ gỗ cẩm lai quý hiếm có màu nâu đỏ đặc trưng. Gỗ cẩm lai có độ cứng vừa phải, không làm tổn thương lưỡi dao, đồng thời có tính kháng khuẩn tự nhiên. Bề mặt được xử lý mịn màng, không thấm nước. Thích hợp cho việc cắt thái thực phẩm hàng ngày hoặc trình bày món ăn.",
         "Tây Nguyên, Đắk Lắk", "Gia công gỗ cẩm lai thủ công", 
         "Gỗ quý Tây Nguyên, truyền thống chế biến gỗ", 
         "Kích thước 40x28x2cm, bo tròn các góc", 
         "Rửa sạch sau khi dùng, thoa dầu ăn dưỡng gỗ hàng tháng",
         "thớt gỗ, cẩm lai, oval, cao cấp, kháng khuẩn, Tây Nguyên"),

        (15, "Giá Để Đũa Tre Trang Trí", "Đồ Gia Dụng", "Tre", 65000, 90,
         "Giá để đũa được chế tác từ tre già, thiết kế nhỏ gọn tiện lợi. Có thể để được 5-6 đôi đũa, thích hợp cho gia đình nhỏ. Tre được chọn lọc kỹ càng, xử lý chống mối mọt. Sản phẩm có thể trang trí thêm họa tiết đơn giản hoặc để nguyên màu tre tự nhiên. Góp phần tạo nên không gian bếp xanh, thân thiện với môi trường.",
         "Làng nghề tre nứa truyền thống", "Gia công tre thủ công", 
         "Văn hóa ẩm thực Việt Nam, sử dụng đũa ăn", 
         "Kích thước 15x8x6cm, có thể để đứng hoặc nằm", 
         "Lau khô sau khi dùng, tránh ngâm nước lâu",
         "giá đũa, tre, trang trí, bếp, thân thiện môi trường, tiện dụng"),

        # TRANH CATEGORY
        (16, "Tranh Thêu Tay Phong Cảnh Hạ Long", "Tranh", "Vải", 850000, 12,
         "Tranh thêu tay mô tả vẻ đẹp hùng vĩ của Vịnh Hạ Long với những hòn đảo đá vôi, thuyền buồm nhỏ và nước biển xanh biếc. Được thêu bằng chỉ tơ tằm cao cấp trên vải lụa trắng, mỗi đường kim mũi chỉ đều được thực hiện tỉ mỉ bởi nghệ nhân có kinh nghiệm. Tranh có khung gỗ cao cấp, kính chống phản quang, thích hợp treo tại phòng khách, văn phòng hoặc làm quà tặng.",
         "Làng thêu truyền thống Việt Nam", "Thêu tay chỉ tơ tằm", 
         "Di sản thiên nhiên thế giới Vịnh Hạ Long, nghệ thuật thêu Việt Nam", 
         "Kích thước 60x40cm, có khung và kính bảo vệ", 
         "Tránh ánh nắng trực tiếp, lau kính nhẹ nhàng",
         "tranh thêu, Hạ Long, phong cảnh, tơ tằm, thủ công, cao cấp"),

        (17, "Tranh Gỗ Khắc Làng Quê Việt", "Tranh", "Gỗ", 1200000, 8,
         "Tranh gỗ khắc nổi mô tả cảnh làng quê Việt Nam yên bình với những mái nhà tranh, cây đa, giếng nước, trâu bò và đồng lúa. Được chạm khắc trên gỗ gụ cao cấp bởi nghệ nhân làng Đông Hồ, Bắc Ninh. Mỗi chi tiết nhỏ đều được chạm khắc tinh xảo, tạo chiều sâu và sự sống động cho bức tranh. Màu gỗ tự nhiên tạo cảm giác ấm áp, gần gũi.",
         "Làng Đông Hồ, Bắc Ninh", "Chạm khắc gỗ nổi truyền thống", 
         "Cảnh làng quê Việt Nam, nghệ thuật chạm khắc dân gian", 
         "Kích thước 80x60x5cm, khắc nổi 3D", 
         "Lau bụi nhẹ nhàng, tránh ẩm ướt và ánh nắng mạnh",
         "tranh gỗ, khắc nổi, làng quê, Đông Hồ, nghệ thuật, gỗ gụ"),

        (18, "Tranh Thêu Hoa Sen Việt Nam", "Tranh", "Vải", 680000, 18,
         "Tranh thêu hoa sen - quốc hoa Việt Nam, biểu tượng của sự thanh cao, thuần khiết và vẻ đẹp tinh thần. Hoa sen được thêu trên nền vải lụa với nhiều sắc màu từ trắng tinh khôi đến hồng nhạt, lá sen xanh tươi. Kỹ thuật thêu phẳng và thêu nổi kết hợp tạo độ sống động cho từng cánh hoa. Thích hợp trang trí phòng thờ, phòng khách hoặc làm quà tặng ý nghĩa.",
         "Làng thêu Việt Nam", "Thêu tay truyền thống", 
         "Hoa sen - quốc hoa Việt Nam, biểu tượng thanh cao", 
         "Kích thước 50x70cm, thêu trên lụa cao cấp", 
         "Bảo quản nơi khô ráo, tránh ánh nắng và độ ẩm cao",
         "tranh thêu, hoa sen, quốc hoa, thanh cao, lụa, truyền thống"),

        (19, "Tranh Sơn Mài Cô Gái Việt", "Tranh", "Gỗ", 950000, 10,
         "Tranh sơn mài mô tả hình ảnh cô gái Việt Nam dịu dàng trong tà áo dài truyền thống. Được vẽ trên nền gỗ với kỹ thuật sơn mài cổ truyền, sử dụng sơn ta và vỏ trứng để tạo độ bóng và màu sắc độc đáo. Hình ảnh cô gái với mái tóc dài, đôi mắt buồn và nụ cười dịu dàng thể hiện vẻ đẹp truyền thống của phụ nữ Việt Nam. Khung tranh bằng gỗ hương thơm tự nhiên.",
         "Hà Nội - cái nôi của sơn mài Việt Nam", "Sơn mài truyền thống với sơn ta và vỏ trứng", 
         "Vẻ đẹp phụ nữ Việt Nam, áo dài truyền thống", 
         "Kích thước 45x60cm, độ dày 2cm", 
         "Lau nhẹ bằng khăn mềm, tránh hóa chất tẩy rửa",
         "sơn mài, cô gái Việt, áo dài, truyền thống, Hà Nội, nghệ thuật"),

        (20, "Tranh Đông Hồ Lợn Đất", "Tranh", "Giấy", 120000, 50,
         "Tranh Đông Hồ truyền thống với hình ảnh con lợn đất - biểu tượng của sự no đủ, thịnh vượng trong văn hóa nông nghiệp Việt Nam. Được in trên giấy dó bằng kỹ thuật khắc gỗ và tô màu thủ công với màu tự nhiên từ lá cây, hoa quả. Màu sắc tươi sáng, nét vẽ mộc mạc thể hiện tính chất dân gian đậm đà. Thường được dán trong nhà vào dịp Tết để cầu may mắn.",
         "Làng Đông Hồ, Bắc Ninh", "Khắc gỗ và tô màu thủ công", 
         "Nghệ thuật dân gian Việt Nam, tranh Tết truyền thống", 
         "Kích thước 30x40cm, giấy dó dày", 
         "Tránh ẩm ướt, có thể ép khung kính bảo quản",
         "Đông Hồ, lợn đất, tranh Tết, dân gian, may mắn, khắc gỗ"),

        # TƯỢNG CATEGORY
        (21, "Tượng Phật Di Lặc Gỗ Hương", "Tượng", "Gỗ", 1500000, 8,
         "Tượng Phật Di Lặc được chạm khắc từ gỗ hương quý hiếm, cao 30cm, thể hiện vẻ từ bi và hạnh phúc của Đức Phật. Gương mặt tươi cười, bụng tròn đầy đặn biểu tượng cho sự no đủ, hạnh phúc và may mắn. Được chạm khắc bởi nghệ nhân lành nghề với từng đường nét tinh xảo, bề mặt được đánh bóng mịn màng. Thích hợp đặt trong phòng thờ, phòng khách hoặc văn phòng để cầu bình an, thịnh vượng.",
         "Làng nghề chạm khắc Đông Anh, Hà Nội", "Chạm khắc gỗ hương thủ công", 
         "Phật giáo Việt Nam, biểu tượng hạnh phúc và thịnh vượng", 
         "Cao 30cm, rộng 25cm, nặng 3kg", 
         "Lau bụi nhẹ nhàng, đặt nơi thoáng mát, tránh ánh nắng trực tiếp",
         "tượng Phật, Di Lặc, gỗ hương, chạm khắc, tâm linh, may mắn"),

        (22, "Tượng Rồng Đá Non Nước", "Tượng", "Đá", 2200000, 5,
         "Tượng rồng được chạm khắc từ đá Non Nước Đà Nẵng nổi tiếng, cao 40cm. Con rồng với thân hình uốn lượn, đầu ngẩng cao, miệng há ra như đang thở lửa, thể hiện sức mạnh và uy quyền. Đá Non Nước có màu trắng xám tự nhiên, kết cấu chắc chắn, không bị phong hóa theo thời gian. Rồng là linh vật thiêng liêng trong văn hóa Việt Nam, biểu tượng cho quyền lực, sức mạnh và sự thịnh vượng.",
         "Làng đá Non Nước, Đà Nẵng", "Chạm khắc đá Non Nước thủ công", 
         "Rồng - linh vật thiêng liêng của dân tộc Việt Nam", 
         "Cao 40cm, dài 60cm, nặng 15kg", 
         "Lau chùi bằng nước sạch, có thể đặt ngoài trời",
         "tượng rồng, đá Non Nước, linh vật, chạm khắc, Đà Nẵng, uy quyền"),

        (23, "Tượng Quan Âm Gỗ Mít", "Tượng", "Gỗ", 1800000, 6,
         "Tượng Quan Thế Âm Bồ Tát được chạm khắc từ gỗ mít già, cao 35cm, thể hiện vẻ từ bi, bao dung của Đức Quan Âm. Tôn tượng có tư thế đứng trang nghiêm, tay cầm bình cam lộ, mặt hiền từ với nụ cười dịu dàng. Gỗ mít có màu vàng ươm tự nhiên, vân gỗ đẹp, độ bền cao và có hương thơm nhẹ. Được nhiều gia đình Việt Nam thờ cúng để cầu bình an, sức khỏe và may mắn.",
         "Làng nghề chạm khắc Đông Anh, Hà Nội", "Chạm khắc gỗ mít thủ công", 
         "Quan Âm Bồ Tát - biểu tượng từ bi trong Phật giáo", 
         "Cao 35cm, rộng 15cm, có đế gỗ", 
         "Thắp nhang cúng, lau bụi định kỳ, đặt nơi trang nghiêm",
         "tượng Quan Âm, gỗ mít, Phật giáo, từ bi, chạm khắc, tâm linh"),

        (24, "Tượng Cặp Chó Đá Phong Thủy", "Tượng", "Đá", 1600000, 10,
         "Cặp tượng chó đá phong thủy được chạm khắc từ đá hoa cương, mỗi con cao 25cm. Một con miệng há, một con miệng khép, tượng trưng cho âm dương cân bằng. Chó đá thường được đặt trước cửa nhà, công ty để trấn yểm, xua đuổi tà khí và mang lại may mắn. Được chạm khắc tỉ mỉ với bộ lông rõ nét, đôi mắt sáng, tư thế oai nghiêm thể hiện sự bảo vệ.",
         "Làng đá Ninh Vân, Ninh Bình", "Chạm khắc đá hoa cương", 
         "Phong thủy Việt Nam, linh vật bảo vệ gia đình", 
         "Mỗi con cao 25cm, dài 30cm, nặng 8kg", 
         "Có thể đặt ngoài trời, định kỳ rửa nước sạch",
         "chó đá, phong thủy, trấn yểm, cặp, hoa cương, bảo vệ"),

        (25, "Tượng Tứ Linh Việt Nam", "Tượng", "Gỗ", 3500000, 3,
         "Bộ tượng Tứ Linh gồm Rồng, Lân, Quy, Phượng được chạm khắc từ gỗ sưa đỏ quý hiếm. Mỗi linh vật cao khoảng 20cm, được đặt trên đế gỗ chung. Tứ Linh là bốn linh vật thiêng liêng nhất trong văn hóa Việt Nam, tượng trưng cho quyền lực (Rồng), nhân từ (Lân), trường thọ (Quy) và đức hạnh (Phượng). Bộ tượng thích hợp đặt trong phòng khách, phòng làm việc của lãnh đạo hoặc làm quà tặng cao cấp.",
         "Làng nghề chạm khắc Sơn Đồng, Hoài Đức", "Chạm khắc gỗ sưa đỏ cao cấp", 
         "Tứ Linh - bốn linh vật thiêng liêng nhất Việt Nam", 
         "Bộ 4 tượng, mỗi con cao 20cm, đế chung 60x20cm", 
         "Bảo quản cẩn thận, tránh va đập, lau bụi nhẹ nhàng",
         "Tứ Linh, Rồng Lân Quy Phượng, gỗ sưa, linh vật, cao cấp, quý hiếm"),

        # Thêm các sản phẩm khác để đủ 50+
        (26, "Nón Cói Bèo Miền Tây", "Nón", "Cói", 75000, 70,
         "Nón cói được đan từ cây cói bèo mọc tự nhiên ở miền Tây Nam Bộ. Cói bèo có sợi mềm mại, dai và có màu xanh tự nhiên đẹp mắt. Nón có form tròn đơn giản, nhẹ, thoáng khí, rất phù hợp với khí hậu nóng ẩm. Được người dân miền Tây sử dụng từ lâu đời, nón cói bèo không chỉ che nắng mà còn có thể úp xuống nước để múc nước trong trường hợp khẩn cấp.",
         "Miền Tây Nam Bộ, vùng đồng bằng sông Cửu Long", "Đan cói bèo truyền thống", 
         "Văn hóa miền Tây, thích ứng khí hậu nhiệt đới", 
         "Đường kính 38cm, nhẹ 150g", 
         "Phơi khô sau khi ướt, bảo quản nơi thoáng mát",
         "nón cói, miền Tây, cói bèo, nhẹ, thoáng khí, truyền thống"),

        (27, "Giỏ Xách Cói Thêu Hoa", "Giỏ", "Cói", 190000, 35,
         "Giỏ xách được đan từ cói tự nhiên và thêu họa tiết hoa văn bằng chỉ màu. Thiết kế hiện đại với quai xách chắc chắn, phù hợp để đi chợ, dạo phố hoặc đi biển. Họa tiết thêu là những bông hoa đơn giản nhưng tinh tế, tạo điểm nhấn cho chiếc giỏ. Sản phẩm vừa thực dụng vừa thời trang, thể hiện sự kết hợp hài hòa giữa truyền thống và hiện đại.",
         "Làng nghề đan cói miền Bắc", "Đan cói và thêu tay", 
         "Kết hợp truyền thống và hiện đại, thời trang bền vững", 
         "Kích thước 30x20x15cm, có quai xách dài 40cm", 
         "Giặt nhẹ bằng nước lạnh, phơi khô tự nhiên",
         "giỏ cói, thêu hoa, xách tay, thời trang, hiện đại, bền vững"),

        (28, "Khay Tre Làm Bánh Chưng", "Đồ Gia Dụng", "Tre", 150000, 40,
         "Khay tre chuyên dụng để làm bánh chưng trong dịp Tết Nguyên Đán. Được đan từ tre già, có nan tre mỏng đan chặt tạo bề mặt phẳng, không thấm nước. Kích thước vừa phải để vo gạo, trải lá dong và gói bánh chưng. Tre được xử lý kỹ càng, sạch sẽ, an toàn thực phẩm. Là dụng cụ không thể thiếu trong bếp ăn truyền thống Việt Nam, đặc biệt trong dịp Tết.",
         "Làng nghề tre nứa Phụ Dực, Hà Nội", "Đan tre chuyên dụng", 
         "Bánh chưng - món ăn truyền thống Tết Việt Nam", 
         "Kích thước 50x35cm, độ dày 1cm", 
         "Rửa sạch sau khi dùng, phơi khô hoàn toàn",
         "khay tre, bánh chưng, Tết, truyền thống, bếp Việt, an toàn thực phẩm"),

        (29, "Hộp Cơm Gỗ Dừa Tròn", "Đồ Gia Dụng", "Gỗ", 95000, 60,
         "Hộp cơm được làm từ gỗ dừa tự nhiên, có nắp đậy kín. Gỗ dừa có tính kháng khuẩn, giữ cơm ấm lâu và không làm biến đổi hương vị thức ăn. Thiết kế tròn truyền thống với họa tiết vân gỗ dừa tự nhiên. Phù hợp để đựng cơm, cháo hoặc các món ăn khác. Sản phẩm thân thiện với môi trường, thay thế tốt cho hộp nhựa.",
         "Miền Tây Nam Bộ, vùng trồng dừa Bến Tre", "Gia công gỗ dừa thủ công", 
         "Tái chế vỏ dừa, zero waste, bảo vệ môi trường", 
         "Đường kính 15cm, cao 8cm, có nắp đậy", 
         "Rửa bằng nước ấm, không dùng xà phòng mạnh",
         "hộp cơm, gỗ dừa, tròn, kháng khuẩn, thân thiện môi trường"),

        (30, "Tranh Lụa Hoa Đào Xuân", "Tranh", "Vải", 420000, 20,
         "Tranh lụa vẽ cành hoa đào nở rộ, biểu tượng của mùa xuân và sự may mắn. Được vẽ trên lụa tơ tằm cao cấp bằng màu acrylic chuyên dụng cho lụa. Cành đào với những bông hoa hồng nhạt, lá xanh non, thể hiện sức sống mãnh liệt của mùa xuân. Tranh thích hợp treo trong dịp Tết Nguyên Đán để trang trí và cầu may mắn cho năm mới.",
         "Làng lụa Vạn Phúc, Hà Đông", "Vẽ lụa truyền thống", 
         "Hoa đào - biểu tượng mùa xuân, Tết Nguyên Đán", 
         "Kích thước 40x60cm, vẽ trên lụa tơ tằm", 
         "Tránh ánh nắng trực tiếp, có thể ép khung kính",
         "tranh lụa, hoa đào, xuân, Tết, may mắn, lụa tơ tằm"),
    ]
    return products

def generate_orders():
    """Generate fixed, deterministic orders."""
    orders = [
        (1, "CUST001", "2025-04-01", "Đang xử lý", 560000),  # 5 Nón Lá Cổ Điển
        (2, "CUST001", "2025-04-10", "Đã giao", 600000),     # 2 Giỏ Tre Quà Tặng
    ]
    return orders

def generate_order_items(orders):
    """Generate fixed order items."""
    order_items = [
        (1, 1, 5, 112000),  # Order 1: 5 Nón Lá Cổ Điển
        (2, 4, 2, 300000),  # Order 2: 2 Giỏ Tre Quà Tặng
    ]
    return order_items, orders

def generate_cart_items():
    """Generate empty cart for testing."""
    carts = [(1, "CUST001", datetime.now(), datetime.now())]
    cart_items = []  # Start empty, let tests add items
    return carts, cart_items

def insert_data(conn, products, orders, order_items, carts, cart_items):
    """Insert generated data into the database."""
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        products
    )
    cursor.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
        orders
    )
    cursor.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?)",
        order_items
    )
    cursor.executemany(
        "INSERT INTO carts VALUES (?, ?, ?, ?)",
        carts
    )
    cursor.executemany(
        "INSERT INTO cart_items VALUES (?, ?, ?, ?)",
        cart_items
    )
    conn.commit()

def setup_database(clear_existing=False):
    """Set up the database with schema and deterministic data."""
    db_file = os.getenv("DB_PATH")
    if clear_existing and os.path.exists(db_file):
        os.remove(db_file)
    
    conn = sqlite3.connect(db_file)
    
    create_schema(conn)
    
    products = generate_products()
    orders = generate_orders()
    order_items, orders = generate_order_items(orders)
    carts, cart_items = generate_cart_items()
    
    insert_data(conn, products, orders, order_items, carts, cart_items)
    
    conn.close()
    print("Database set up successfully!")
    return db_file

if __name__ == "__main__":
    db = setup_database(clear_existing=True)