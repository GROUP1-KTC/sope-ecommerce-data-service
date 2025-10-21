from typing import Optional, Dict, Any, List

import httpx
from langchain.tools import tool

from app.features.chatbot.integrations.backend_client import BackendClient

def _safe_json(response: httpx.Response) -> Dict[str, Any]:
    try:
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {"raw": response.text}

def _extract_products(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "products", "content", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []

def _filter_products(
    products: List[Dict[str, Any]],
    min_price: Optional[float],
    max_price: Optional[float],
) -> List[Dict[str, Any]]:
    if min_price is None and max_price is None:
        return products

    filtered: List[Dict[str, Any]] = []
    for product in products:
        price_raw = product.get("minPrice")
        try:
            price_value = float(price_raw) if price_raw is not None else None
        except (TypeError, ValueError):
            price_value = None

        if min_price is not None and (price_value is None or price_value < min_price):
            continue
        if max_price is not None and (price_value is None or price_value > max_price):
            continue
        filtered.append(product)
    return filtered

@tool
async def browse_catalog(
    search_keyword: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Search for products by keyword with optional price filtering.
    
    Always call this first when user mentions they want to find or search for something.
    Returns a list of matching products for further refinement.
    
    Args:
        search_keyword: Product search term (e.g., "laptop", "áo thun", "giày")
        min_price: Minimum price in VND (optional)
        max_price: Maximum price in VND (optional)
    
    Returns:
        Dictionary with 'keyword', 'filters', and 'products' array containing:
        - id: product_id
        - name: product name
        - minPrice: lowest variant price
        - rating: average rating
        - reviewCount: number of reviews
        - inStock: availability
    
    Example:
        Input: search_keyword="laptop", max_price=15000000
        Output: {"keyword": "laptop", "products": [...30 products...]}
    """
    keyword = (search_keyword or "").strip()
    if not keyword:
        return {"error": "Vui lòng cung cấp từ khóa tìm kiếm."}

    client = BackendClient()
    try:
        payload = await client.search_products_by_name(keyword)
        products = _extract_products(payload)
        products = _filter_products(products, min_price, max_price)
        return {
            "keyword": keyword,
            "filters": {"min_price": min_price, "max_price": max_price},
            "products": products,
        }
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể tìm kiếm sản phẩm.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối khi tìm kiếm sản phẩm.", "details": str(exc)}

@tool
async def get_product_info(
    product_id: str,
) -> Dict[str, Any]:
    """
    Get basic product information including variants, price, and shop details.
    
    Call this when user wants to see product details, price, specifications, variants, or shop info.
    
    Args:
        product_id: Unique product identifier (from browse_catalog results)
    
    Returns:
        Dictionary containing:
        - id: product ID
        - name: product name
        - description: detailed description
        - price: current price
        - minPrice: minimum price
        - rating: average rating
        - reviewCount: total number of reviews
        - variants: list of available variants (color, size, etc.)
        - images: product images
        - shop: shop information (name, rating, response time)
        - inStock: availability status
        - specs: technical specifications
    
    Example:
        Input: product_id="p123"
        Output: {
            "id": "p123",
            "name": "Laptop ABC",
            "price": 12900000,
            "rating": 4.8,
            "reviewCount": 230,
            "variants": [{"color": "xanh", "size": "15 inch", "variantId": "var1"}, ...],
            "shop": {"name": "Shop XYZ", "rating": 4.9}
        }
    """
    product_id = (product_id or "").strip()
    if not product_id:
        return {"error": "Cần cung cấp product_id."}

    client = BackendClient()
    try:
        product = await client.get_product_by_id(product_id)
        if not isinstance(product, dict):
            return {"error": "Không tìm thấy sản phẩm.", "product_id": product_id}

        return product
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể lấy thông tin sản phẩm.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối.", "details": str(exc)}


@tool
async def get_product_reviews(
    product_id: str,
    min_rating: Optional[int] = None,
    max_reviews: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get customer reviews and ratings for a specific product.
    
    Call this when user asks about reviews, ratings, customer feedback, or what people say about the product.
    
    Args:
        product_id: Product ID (from browse_catalog or get_product_info)
        min_rating: Filter reviews by minimum rating (1-5 stars) (optional)
        max_reviews: Maximum number of reviews to return (optional)
    
    Returns:
        Dictionary containing:
        - reviews: Array of review objects:
            * rating: review rating (1-5)
            * text: review comment
            * author: reviewer name
            * date: review date
            * helpful: helpful count
        - averageRating: average rating across all reviews
        - totalReviews: total number of reviews
        - ratingDistribution: breakdown by star (1-5 stars)
        - topReviews: most helpful reviews
    
    Example:
        Input: product_id="p123", min_rating=4, max_reviews=5
        Output: {
            "reviews": [
                {"rating": 5, "text": "Sản phẩm tốt", "author": "Nguyễn A", "date": "2024-10-20"},
                {"rating": 4, "text": "Hợp lý", "author": "Trần B", "date": "2024-10-19"}
            ],
            "averageRating": 4.5,
            "totalReviews": 230
        }
    """
    product_id = (product_id or "").strip()
    if not product_id:
        return {"error": "Cần cung cấp product_id."}

    client = BackendClient()
    try:
        reviews_payload = await client.get_product_reviews(product_id)
        reviews_list = (
            reviews_payload.get("reviews", [])
            if isinstance(reviews_payload, dict)
            else reviews_payload
        )
        if not isinstance(reviews_list, list):
            reviews_list = []

        if min_rating is not None:
            reviews_list = [
                rv for rv in reviews_list if int(rv.get("rating", 0) or 0) >= min_rating
            ]
        if max_reviews:
            reviews_list = reviews_list[:max_reviews]

        if reviews_list:
            avg_rating = sum(float(rv.get("rating", 0) or 0) for rv in reviews_list) / len(reviews_list)
        else:
            avg_rating = (
                reviews_payload.get("averageRating")
                if isinstance(reviews_payload, dict)
                else None
            )

        return {
            "reviews": reviews_list,
            "averageRating": round(avg_rating, 1) if avg_rating else None,
            "totalReviews": reviews_payload.get("totalReviews", len(reviews_list)) if isinstance(reviews_payload, dict) else len(reviews_list),
            "filters": {"min_rating": min_rating, "max_reviews": max_reviews},
        }
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể lấy review.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối.", "details": str(exc)}


@tool
async def get_product_discounts(
    product_id: str,
) -> Dict[str, Any]:
    """
    Get active discounts and promotions for a specific product.
    
    Call this when user asks about discounts, promotions, offers, or sale prices.
    
    Args:
        product_id: Product ID (from browse_catalog or get_product_info)
    
    Returns:
        Dictionary containing:
        - platformDiscounts: Platform-wide promotions applicable to this product
            * name: promotion name
            * description: what the promotion includes
            * discount: discount value or percentage
            * validUntil: expiration date
        - shopDiscounts: Shop-specific promotions from the seller
            * name: promotion name
            * discount: discount amount
            * conditions: conditions to apply
        - applicableVouchers: Available vouchers user can use
        - hasFlashSale: Whether product is in flash sale
        - totalSavings: Total potential savings
    
    Example:
        Input: product_id="p123"
        Output: {
            "platformDiscounts": [
                {"name": "Giảm 10% tối thiểu đơn 1M", "discount": "10%", "validUntil": "2024-10-31"}
            ],
            "shopDiscounts": [
                {"name": "Khuyến mãi shop", "discount": 500000, "conditions": "Có điều kiện"}
            ],
            "applicableVouchers": ["VC123", "VC456"],
            "totalSavings": 1500000
        }
    """
    product_id = (product_id or "").strip()
    if not product_id:
        return {"error": "Cần cung cấp product_id."}

    client = BackendClient()
    try:
        discounts: Dict[str, Any] = {}

        # Get platform discounts
        platform_raw = await client.get_active_discounts()
        platform_promos = (
            platform_raw.get("promotions", platform_raw)
            if isinstance(platform_raw, dict)
            else platform_raw
        )
        if isinstance(platform_promos, list):
            discounts["platformDiscounts"] = platform_promos

        # Get product info to get shop ID
        product = await client.get_product_by_id(product_id)
        shop_raw = product.get("shop") or {}
        shop_id = shop_raw.get("id") or shop_raw.get("shopId")

        # Get shop discounts
        if shop_id:
            shop_promos_raw = await client.get_shop_active_discounts(str(shop_id))
            if isinstance(shop_promos_raw, dict):
                shop_promos = (
                    shop_promos_raw.get("data")
                    or shop_promos_raw.get("discounts")
                    or shop_promos_raw.get("promotions")
                    or []
                )
            else:
                shop_promos = shop_promos_raw
            if isinstance(shop_promos, list):
                discounts["shopDiscounts"] = shop_promos

        return discounts if discounts else {"message": "Không có khuyến mãi nào cho sản phẩm này."}

    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể lấy thông tin khuyến mãi.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối.", "details": str(exc)}

@tool
async def add_item_to_cart(
    product_variant_id: str,
    quantity: int = 1,
    image: Optional[str] = None,
    user_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Add a product variant to user's shopping cart.
    
    Call this when user confirms they want to add a product to their cart.
    IMPORTANT: DO NOT provide user_token - it will be AUTOMATICALLY INJECTED by the system.
    Only pass product_variant_id, quantity, and image.
    
    Args:
        product_variant_id: Specific variant ID (e.g., "var456" for color/size combo)
        quantity: Number of items to add (default 1)
        image: Product image URL (optional)
        user_token: DO NOT USE - will be auto-injected by system (keep as default)
    
    Returns:
        Dictionary with:
        - success: Boolean indicating if item was added
        - message: Confirmation or error message
        - errors: List of error details (if any)
        - status_code: HTTP status code
    
    Example:
        Input: product_variant_id="var456", quantity=2, user_token="token123"
        Output: {"success": true, "message": "Added 2 items to cart"}
    """
    if not user_token:
        return {"error": "Cần đăng nhập (user_token) để thêm vào giỏ hàng."}
    variant_id = (product_variant_id or "").strip()
    if not variant_id:
        return {"error": "Thiếu product_variant_id. Vui lòng chọn biến thể cụ thể."}
    if quantity <= 0:
        return {"error": "Số lượng phải lớn hơn 0."}

    client = BackendClient(user_token)
    try:
        response = await client.add_to_cart(
            product_variant_id=variant_id,
            quantity=quantity,
            image=image,
            user_token=user_token,
        )
        success = bool(response.get("success", True))
        return {
            "success": success,
            "message": response.get("message"),
            "errors": response.get("errors", []),
            "status_code": response.get("statusCode"),
        }
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể thêm sản phẩm vào giỏ hàng.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối khi thêm sản phẩm vào giỏ hàng.", "details": str(exc)}

@tool
async def list_orders(
    user_token: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve user's order list with optional status filtering.
    
    Call this when user asks about their orders, order history, or wants to see their past purchases.
    User must be logged in (will be auto-verified by system).
    
    USAGE: Call this tool ONLY with status_filter parameter (if needed).
    Example: list_orders(status_filter="pending")
    Do NOT pass user_token - it will be auto-injected by the system.
    
    Args:
        user_token: SYSTEM PARAMETER - Never pass this, it's auto-injected
        status_filter: Optional status filter (values: "pending", "processing", "shipped", "delivered", "cancelled")
    
    Returns:
        Dictionary containing:
        - orders: List of order objects, each with:
            * orderNumber: order code (e.g., "ORDER001")
            * status: current status (pending/processing/shipped/delivered/cancelled)
            * totalAmount: order total price in VND
            * date: order creation date
            * items: list of products ordered
        - total: total number of orders (after applying filter)
        - filter_applied: which status filter was used
    
    Example calls:
        • "Tôi muốn xem order của tôi" → list_orders()
        • "Xem order pending của tôi" → list_orders(status_filter="pending")
        • "Những order nào chưa giao?" → list_orders(status_filter="processing")
    """
    if not user_token:
        return {"error": "Cần đăng nhập để xem đơn hàng."}

    client = BackendClient(user_token)
    try:
        orders_payload = await client.get_my_orders(user_token)
        orders = orders_payload.get("orders", []) if isinstance(orders_payload, dict) else []
        if status_filter:
            key = status_filter.lower()
            orders = [order for order in orders if str(order.get("status", "")).lower() == key]
        return {
            "orders": orders,
            "total": len(orders),
            "filter_applied": status_filter,
        }
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể lấy danh sách đơn hàng.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối khi lấy danh sách đơn hàng.", "details": str(exc)}

@tool
async def track_order(
    order_number: str,
    user_token: Optional[str] = None,
    include_history: bool = True,
) -> Dict[str, Any]:
    """
    Track a specific order and get detailed status information.
    
    Call this when user asks about a specific order's status or tracking information.
    IMPORTANT: DO NOT provide user_token - it will be AUTOMATICALLY INJECTED by the system.
    Only pass order_number and include_history.
    
    Args:
        order_number: Order ID/number to track (e.g., "2024-001")
        user_token: DO NOT USE - will be auto-injected by system (keep as default)
        include_history: Include status history timeline (default True)
    
    Returns:
        Dictionary containing:
        - order: Full order details (items, prices, addresses, dates)
        - items: List of items in the order with:
            * name: product name
            * quantity: qty ordered
            * price: unit price
            * variantInfo: selected color, size, etc.
        - status_history: Timeline of order status changes (if include_history=True)
            * status: order status at time
            * timestamp: when status changed
            * notes: additional info
    
    Example:
        Input: order_number="2024-001"  (NO user_token needed!)
        Output: {
            "order": {...order details...},
            "status_history": [
                {"status": "confirmed", "timestamp": "2024-10-20"},
                {"status": "shipped", "timestamp": "2024-10-21"},
                {"status": "in_delivery", "timestamp": "2024-10-22"}
            ]
        }
    """
    if not user_token:
        return {"error": "Cần đăng nhập (user_token) để tra cứu đơn hàng."}
    order_number = (order_number or "").strip()
    if not order_number:
        return {"error": "Vui lòng cung cấp mã đơn hàng hợp lệ."}

    client = BackendClient(user_token)
    try:
        order_data = await client.track_order(order_number, user_token)
        if not isinstance(order_data, dict):
            return {"error": "Không tìm thấy đơn hàng với mã đã nhập."}

        result: Dict[str, Any] = {
            "order": order_data,
            "items": order_data.get("items", []),
        }
        if include_history:
            history = order_data.get("statusHistory") or order_data.get("status_history") or []
            result["status_history"] = history
        return result
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể tra cứu đơn hàng.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối khi tra cứu đơn hàng.", "details": str(exc)}

def get_tools(user_token: Optional[str] = None) -> List:
    """
    Công bố các tool dành cho chatbot.
    Duy trì danh sách ngắn gọn để agent dễ chọn đúng thao tác.
    
    Tools:
    - browse_catalog: Tìm sản phẩm theo từ khóa
    - get_product_info: Lấy thông tin cơ bản sản phẩm (giá, specs, variant)
    - get_product_reviews: Lấy review & rating sản phẩm
    - get_product_discounts: Lấy khuyến mãi & offer cho sản phẩm
    - add_item_to_cart: Thêm sản phẩm vào giỏ hàng
    - list_orders: Xem danh sách đơn hàng
    - track_order: Tra cứu chi tiết đơn hàng
    """
    return [
        browse_catalog,
        get_product_info,
        get_product_reviews,
        get_product_discounts,
        add_item_to_cart,
        list_orders,
        track_order,
    ]
