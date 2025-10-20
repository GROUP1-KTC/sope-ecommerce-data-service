from typing import Optional, Dict, Any, List

import httpx
from langchain.tools import tool

from app.features.chatbot.integrations.backend_client import BackendClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Catalog & Product
# ---------------------------------------------------------------------------


@tool
async def browse_catalog(
    search_keyword: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Tìm sản phẩm theo từ khóa (có thể lọc giá).
    Dùng để lấy danh sách sản phẩm và chuẩn bị cho bước chọn chi tiết.
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
async def product_details(
    product_id: str,
    include_variants: bool = True,
    include_reviews: bool = False,
    include_discounts: bool = False,
    include_shop: bool = False,
    min_rating: Optional[int] = None,
    max_reviews: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết sản phẩm (biến thể, đánh giá, khuyến mãi, shop).
    Cần truyền product_id hợp lệ lấy từ browse_catalog.
    """
    product_id = (product_id or "").strip()
    if not product_id:
        return {"error": "Cần cung cấp product_id để tra cứu chi tiết sản phẩm."}

    client = BackendClient()
    try:
        product = await client.get_product_by_id(product_id)
        if not isinstance(product, dict):
            return {"error": "Không tìm thấy sản phẩm với mã đã chọn.", "product_id": product_id}

        response: Dict[str, Any] = {"product": product}

        variants = product.get("variants", []) or []
        if include_variants:
            response["variants"] = variants

        if include_reviews:
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
            response["reviews"] = {
                "items": reviews_list,
                "summary": {
                    "count": len(reviews_list),
                    "average_rating": avg_rating,
                    "filters": {"min_rating": min_rating, "max_reviews": max_reviews},
                },
            }

        if include_discounts:
            discounts: Dict[str, Any] = {}
            platform_raw = await client.get_active_discounts()
            platform_promos = (
                platform_raw.get("promotions", platform_raw)
                if isinstance(platform_raw, dict)
                else platform_raw
            )
            if isinstance(platform_promos, list):
                discounts["platform"] = platform_promos

            shop_raw = product.get("shop") or {}
            shop_id = shop_raw.get("id") or shop_raw.get("shopId")
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
                    discounts["shop"] = shop_promos
            response["discounts"] = discounts

        if include_shop:
            shop_raw = product.get("shop") or {}
            shop_id = shop_raw.get("id") or shop_raw.get("shopId")
            if shop_id:
                response["shop"] = await client.get_shop_info(str(shop_id))

        return response
    except httpx.HTTPStatusError as exc:
        data = _safe_json(exc.response)
        return {
            "error": "Không thể lấy thông tin sản phẩm.",
            "status_code": exc.response.status_code,
            "details": data,
        }
    except httpx.HTTPError as exc:
        return {"error": "Lỗi kết nối khi lấy thông tin sản phẩm.", "details": str(exc)}


# ---------------------------------------------------------------------------
# Account actions (tách tool riêng để agent dễ hiểu luồng)
# ---------------------------------------------------------------------------


@tool
async def add_item_to_cart(
    product_variant_id: str,
    quantity: int = 1,
    image: Optional[str] = None,
    user_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Thêm biến thể sản phẩm vào giỏ hàng (cần user_token hợp lệ)."""
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
    """Liệt kê đơn hàng của người dùng (cần user_token)."""
    if not user_token:
        return {"error": "Cần đăng nhập (user_token) để xem đơn hàng."}

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
    """Tra cứu chi tiết một đơn hàng (cần user_token và order_number)."""
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


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------


def get_tools(user_token: Optional[str] = None) -> List:
    """
    Công bố các tool dành cho chatbot.
    Duy trì danh sách ngắn gọn để agent dễ chọn đúng thao tác.
    """
    return [
        browse_catalog,
        product_details,
        add_item_to_cart,
        list_orders,
        track_order,
    ]
