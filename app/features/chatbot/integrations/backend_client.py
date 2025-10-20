import httpx
from typing import Optional, Dict, Any
from app.configs.settings import settings


class BackendClient:
    def __init__(self, user_token: Optional[str] = None):
        self.base_url = settings.backend_api_url
        self.headers = {
            "Content-Type": "application/json",
        }
        if user_token:
            self.headers["Authorization"] = f"Bearer {user_token}"

    async def get_product_reviews(self, product_id: str) -> Dict[str, Any]:
        """Get product reviews"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/review/{product_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                total = len(data)
                avg_rating = sum(r.get("rating", 0) for r in data) / total if total > 0 else 0
                return {"reviews": data, "totalReviews": total, "averageRating": round(avg_rating, 1)}
            return data
    
    async def get_my_orders(self, user_token: str) -> Dict[str, Any]:
        """Get all orders of current user (requires authentication)"""
        headers = self.headers.copy()
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/orders/user",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            # Backend returns ApiResponse<List<OrderResponse>>
            if isinstance(data, dict) and "data" in data:
                orders = data["data"]
                return {"orders": orders if isinstance(orders, list) else [orders]}
            if isinstance(data, list):
                return {"orders": data}
            return data
    
    async def track_order(self, order_number: str, user_token: str) -> Dict[str, Any]:
        """Track specific order status (requires authentication)"""
        headers = self.headers.copy()
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/orders/{order_number}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            # Backend returns ApiResponse<OrderResponse>
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data
    
    async def get_active_discounts(self) -> Dict[str, Any]:
        """Get active platform discounts"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/discounts/platform/active",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return {"promotions": data["data"]}
            if isinstance(data, list):
                return {"promotions": data}
            return data
    
    async def search_products_by_name(self, name: str) -> Dict[str, Any]:
        """Search products by name"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/products/search-by-name",
                params={"name": name},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Get full product information by product id"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/products/id/{product_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_shop_active_discounts(self, shop_id: str) -> Dict[str, Any]:
        """Get active discounts for a given shop"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/discounts/shops/{shop_id}/active",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return {"discounts": data["data"]}
            if isinstance(data, list):
                return {"discounts": data}
            return data

    async def add_to_cart(
        self,
        product_variant_id: str,
        quantity: int,
        image: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a product variant to the authenticated user's cart"""
        headers = self.headers.copy()
        if user_token:
            headers["Authorization"] = (
                user_token if user_token.lower().startswith("bearer ")
                else f"Bearer {user_token}"
            )

        payload: Dict[str, Any] = {
            "productVariantId": product_variant_id,
            "quantity": quantity,
        }
        if image:
            payload["image"] = image

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/cart",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
