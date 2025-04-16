from difflib import SequenceMatcher
import re
from typing import Dict, List, Tuple, Union, Any

from constants import MATERIALS, CATEGORIES

def similar(a: str, b: str, threshold: float = 0.6) -> bool:
    """Check if two strings are similar using fuzzy matching."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold

def get_intent_score(
    query: str,
    keywords: Dict[str, List[str]],
    patterns: List[str] = None,
    weights: Dict[str, float] = None
) -> float:
    """Calculate intent matching score for a query."""
    if weights is None:
        weights = {
            "exact": 1.0,
            "fuzzy": 0.5,
            "pattern": 2.0
        }
    
    score = 0.0
    query = query.lower()
    
    for lang, word_list in keywords.items():
        for keyword in word_list:
            if keyword in query:
                score += weights["exact"]
            elif any(similar(keyword, word) for word in query.split()):
                score += weights["fuzzy"]
    
    if patterns:
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += weights["pattern"]
    
    return score

def find_best_intent(
    query: str,
    intent_configs: Dict[str, Dict[str, Any]],
    threshold: float = 0.5
) -> Tuple[str, float]:
    """Find the best matching intent for a query."""
    scores = {}
    
    for intent_name, config in intent_configs.items():
        score = get_intent_score(
            query,
            config.get("keywords", {}),
            config.get("patterns", []),
            config.get("weights", None)
        )
        scores[intent_name] = score
    
    if not scores:
        return None, 0.0
    
    best_intent = max(scores.items(), key=lambda x: x[1])
    if best_intent[1] < threshold:
        return None, 0.0
        
    return best_intent

POLICY_INTENTS = {
    "shipping": {
        "keywords": {
            "vi": [
                "vận chuyển", "giao hàng", "ship", "gửi hàng", "vận đơn",
                "phí ship", "thời gian giao", "giao nhanh", "giao chậm",
                "giao hàng tận nơi", "giao đến", "gửi đến"
            ],
            "en": [
                "shipping", "delivery", "ship", "send", "transport",
                "shipping fee", "delivery time", "express", "standard delivery",
                "home delivery", "deliver to", "send to"
            ]
        },
        "patterns": [
            r"(?:mất|tốn|mất khoảng|tốn khoảng).*(?:bao lâu|ngày|giờ)",
            r"(?:phí|giá|chi phí).*(?:vận chuyển|giao|ship)",
            r"(?:giao|ship).*(?:đến|tới|về)",
            r"how.*(?:long|much).*(?:deliver|ship)",
            r"(?:shipping|delivery).*(?:cost|fee|time)"
        ]
    },
    "returns": {
        "keywords": {
            "vi": [
                "đổi trả", "hoàn trả", "trả lại", "đổi hàng", "hoàn tiền",
                "bảo đảm", "không vừa ý", "không hài lòng", "lỗi", "hư hỏng",
                "không đúng", "không phù hợp", "đổi size", "đổi màu"
            ],
            "en": [
                "return", "refund", "exchange", "money back", "guarantee",
                "warranty", "not satisfied", "damaged", "wrong", "defective",
                "doesn't fit", "change size", "change color"
            ]
        },
        "patterns": [
            r"(?:muốn|có thể|được|cho).*(?:đổi|trả)",
            r"(?:nếu|trường hợp).*(?:không vừa|không thích|không hài lòng)",
            r"(?:can|possible).*(?:return|exchange|refund)",
            r"(?:if|when).*(?:not satisfied|wrong|damaged)"
        ]
    }
}

PRODUCT_SEARCH_INTENTS = {
    "by_category": {
        "keywords": {
            "vi": [
                "danh mục", "loại", "thể loại", "phân loại", "hàng", "món",
                "đồ trang trí", "đồ thủ công", "quà tặng"
            ] + CATEGORIES,
            "en": [
                "category", "type", "classification", "item", "product",
                "decoration", "handicraft", "gift"
            ]
        },
        "patterns": [
            r"(?:tìm|xem|mua|sản phẩm).*(?:loại|danh mục|hàng|món|nón|giỏ|tranh|tượng|đồ gia dụng|trang trí|quà)",
            r"(?:search|find|show|buy).*(?:category|type|item|decoration|gift|nón|giỏ|tranh|tượng)"
        ],
        "weights": {"exact": 1.0, "fuzzy": 0.6, "pattern": 1.5}
    },
    "by_price": {
        "keywords": {
            "vi": [
                "giá", "tiền", "chi phí", "rẻ", "đắt", "khoảng giá",
                "rẻ nhất", "đắt nhất", "thấp nhất", "cao nhất", "tầm giá"
            ],
            "en": [
                "price", "cost", "cheap", "expensive", "range",
                "cheapest", "most expensive", "lowest", "highest", "budget"
            ]
        },
        "patterns": [
            r"(?:dưới|trên|khoảng|tầm).*(?:\d+k|\d+\s*nghìn|\d+\s*triệu)",
            r"(?:từ|between).*\d+k.*(?:đến|to).*\d+k",
            r"(?:under|over|about|around).*(?:\$\d+|\d+\s*dollars)",
            r"(?:rẻ nhất|thấp nhất|cheapest|lowest)",
            r"(?:đắt nhất|cao nhất|most expensive|highest)"
        ],
        "weights": {"exact": 1.2, "fuzzy": 0.5, "pattern": 2.0}
    },
    "by_material": {
        "keywords": {
            "vi": MATERIALS + ["gỗ tự nhiên", "tre tự nhiên", "vải thủ công"],
            "en": [m.lower() for m in MATERIALS] + ["natural wood", "natural bamboo", "handwoven fabric"]
        },
        "patterns": [
            r"(?:tìm|xem|mua|sản phẩm).*(?:lá cọ|tre|gỗ|vải|mây|đá|tự nhiên|thủ công)",
            r"(?:search|find|show|buy).*(?:bamboo|wood|fabric|rattan|stone|natural|handmade)"
        ],
        "weights": {"exact": 1.0, "fuzzy": 0.5, "pattern": 1.5}
    },
    "by_quantity": {
        "keywords": {
            "vi": ["số lượng", "bao nhiêu", "mấy", "cái", "sản phẩm", "món"],
            "en": ["quantity", "how many", "number", "items", "products"]
        },
        "patterns": [
            r"(?:\d+\s*(?:cái|sản phẩm|món))",
            r"(?:một vài|một ít|vài|several|few|some)\s*(?:sản phẩm|món|items|products)"
        ],
        "weights": {"exact": 0.8, "fuzzy": 0.4, "pattern": 1.8}
    },
    "by_vague": {
        "keywords": {
            "vi": ["gì đó", "bất kỳ", "cái gì", "món gì", "hàng gì", "quà tặng"],
            "en": ["something", "anything", "whatever", "gift", "item"]
        },
        "patterns": [
            r"(?:tìm|xem|mua).*(?:gì đó|bất kỳ|cái gì|món gì|hàng gì|quà)",
            r"(?:search|find|show|buy).*(?:something|anything|whatever|gift)"
        ],
        "weights": {"exact": 0.7, "fuzzy": 0.3, "pattern": 1.2}
    }
}

ORDER_INTENTS = {
    "check_status": {
        "keywords": {
            "vi": ["trạng thái", "tình trạng", "theo dõi", "đơn hàng", "kiểm tra"],
            "en": ["status", "track", "order", "check"]
        },
        "patterns": [
            r"(?:kiểm tra|xem|theo dõi).*(?:đơn|hàng)",
            r"(?:check|track).*(?:order|status)"
        ]
    },
    "cancel_order": {
        "keywords": {
            "vi": ["hủy", "không mua", "không đặt"],
            "en": ["cancel", "stop", "remove"]
        },
        "patterns": [
            r"(?:muốn|cần|cho).*(?:hủy|không mua)",
            r"(?:want|need|please).*(?:cancel|stop)"
        ]
    }
}