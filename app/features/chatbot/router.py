# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, List, Any
import uuid

from app.features.chatbot.schemas import ChatRequest, ChatResponse
from app.features.chatbot.agent.react_graph import ReActChatbotGraph

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# In-memory storage for demo (single-instance only)
_memory_store: Dict[str, List[Dict[str, str]]] = {}
_session_cache: Dict[str, List[str]] = {}
_session_refs: Dict[str, Dict[str, Any]] = {}
MAX_SESSIONS = 100  # Limit memory usage
MAX_HISTORY = 20    # Messages per session
MAX_CACHE_LINES = 10


def _get_session_refs(session_id: str) -> Dict[str, Any]:
    state = _session_refs.setdefault(
        session_id,
        {
            "products": {},
            "variants": {},
            "product_counter": 0,
            "variant_counter": 0,
        },
    )
    return state


def _map_product(session_id: str, product: Dict[str, Any]) -> Optional[str]:
    product_id = str(product.get("productId") or "").strip()
    if not product_id:
        return None
    state = _get_session_refs(session_id)
    code = state["products"].get(product_id)
    if not code:
        state["product_counter"] += 1
        code = f"P{state['product_counter']}"
        state["products"][product_id] = code
    return code


def _map_variant(session_id: str, variant: Dict[str, Any]) -> Optional[str]:
    variant_id = str(variant.get("productVariantId") or "").strip()
    if not variant_id:
        return None
    state = _get_session_refs(session_id)
    code = state["variants"].get(variant_id)
    if not code:
        state["variant_counter"] += 1
        code = f"V{state['variant_counter']}"
        state["variants"][variant_id] = code
    return code


def _summaries_from_tool_outputs(session_id: str, outputs: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for entry in outputs:
        tool_name = (entry.get("name") or "").lower()
        payload = entry.get("output")
        if not isinstance(payload, dict):
            continue

        if tool_name == "browse_catalog":
            for product in payload.get("products") or []:
                ref = _map_product(session_id, product)
                if not ref:
                    continue
                name = product.get("name") or "Sản phẩm"
                min_price = product.get("minPrice")
                price_info = f" (giá từ {min_price:,} VND)" if isinstance(min_price, (int, float)) else ""
                product_id = product.get("productId")
                id_info = f" [productId={product_id}]" if product_id else ""
                lines.append(f"{ref}: {name}{price_info}{id_info}")

        elif tool_name == "product_insights":
            product = payload.get("product") or {}
            ref = _map_product(session_id, product)
            if ref:
                name = product.get("name") or "Sản phẩm"
                stock = payload.get("availability", {}).get("total_stock")
                stock_info = f", tồn {stock}" if isinstance(stock, (int, float)) else ""
                product_id = product.get("productId")
                id_info = f" [productId={product_id}]" if product_id else ""
                lines.append(f"{ref}: {name}{stock_info}{id_info}")

            for variant in payload.get("variants") or []:
                variant_ref = _map_variant(session_id, variant)
                if not variant_ref:
                    continue
                attrs = variant.get("attributes") or []
                attr_desc = ", ".join(
                    f"{attr.get('name')}: {attr.get('value')}"
                    for attr in attrs
                    if attr.get("name") and attr.get("value")
                ) or "Biến thể"
                price = variant.get("price")
                price_desc = f", giá {price:,} VND" if isinstance(price, (int, float)) else ""
                variant_id = variant.get("productVariantId")
                id_info = f" [variantId={variant_id}]" if variant_id else ""
                lines.append(f"{variant_ref}: {attr_desc}{price_desc}{id_info}")

            reviews = payload.get("reviews")
            if isinstance(reviews, dict):
                summary = reviews.get("summary") or {}
                count = summary.get("count")
                avg = summary.get("average_rating")
                count_info = f"{count} đánh giá" if isinstance(count, int) else "Đánh giá"
                avg_info = f", trung bình {avg}/5" if isinstance(avg, (int, float)) else ""
                product_id = product.get("productId")
                state = _get_session_refs(session_id)
                ref = state["products"].get(product_id)
                if ref:
                    lines.append(f"{ref}: {count_info}{avg_info}")

            discounts = payload.get("discounts")
            if isinstance(discounts, dict):
                platform_promos = discounts.get("platform") or []
                shop_promos = discounts.get("shop") or []
                info_parts = []
                if platform_promos:
                    info_parts.append(f"{len(platform_promos)} ưu đãi nền tảng")
                if shop_promos:
                    info_parts.append(f"{len(shop_promos)} ưu đãi từ shop")
                info_desc = ", ".join(info_parts) if info_parts else "Không có ưu đãi"
                product_id = product.get("productId")
                state = _get_session_refs(session_id)
                ref = state["products"].get(product_id)
                if ref:
                    lines.append(f"{ref}: {info_desc}")

        # account_action outputs đều đã là thông báo cho người dùng, không cần cache thêm.

    return lines


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Chat endpoint for RAG + Agent chatbot
    
    - Supports conversation memory via session_id
    - Uses JWT token for authenticated actions
    - Combines RAG (Knowledge Base) and Agent (Tools) capabilities
    """
    try:
        # Extract token from Authorization header
        user_token = request.user_token
        if not user_token and authorization and authorization.startswith("Bearer "):
            user_token = authorization.removeprefix("Bearer ").strip()
        
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize graph
        graph = ReActChatbotGraph(user_token=user_token)
        
        history = _memory_store.get(session_id, []).copy()
        cached_context = _session_cache.get(session_id, [])
        augmented_message = request.message
        if cached_context:
            context_block = "\n".join(cached_context[-3:])
            augmented_message = (
                f"Ngữ cảnh đã biết:\n{context_block}\n\nNgười dùng: {request.message}"
            )
        
        # Run the graph with existing history
        result = await graph.run(augmented_message, session_id, history)
        
        # Update conversation history
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": result["response"]})
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
        
        # Limit total sessions (FIFO eviction for demo)
        if len(_memory_store) >= MAX_SESSIONS and session_id not in _memory_store:
            oldest_session = next(iter(_memory_store))
            del _memory_store[oldest_session]
            if oldest_session in _session_cache:
                del _session_cache[oldest_session]
            if oldest_session in _session_refs:
                del _session_refs[oldest_session]
        
        _memory_store[session_id] = history
        tool_outputs = result.get("tool_outputs") or []
        if tool_outputs:
            summaries = _summaries_from_tool_outputs(session_id, tool_outputs)
            if summaries:
                cache_entries = _session_cache.setdefault(session_id, [])
                cache_entries.extend(summaries)
                if len(cache_entries) > MAX_CACHE_LINES:
                    _session_cache[session_id] = cache_entries[-MAX_CACHE_LINES:]

        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            sources=result.get("sources"),
            tool_calls=result.get("tool_calls"),
            tool_outputs=result.get("tool_outputs"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")


@router.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    """Clear conversation history for a session"""
    try:
        if session_id in _memory_store:
            del _memory_store[session_id]
        if session_id in _session_cache:
            del _session_cache[session_id]
        if session_id in _session_refs:
            del _session_refs[session_id]
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat: {str(e)}")
