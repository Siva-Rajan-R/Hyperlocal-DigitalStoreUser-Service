import httpx
from typing import Optional, Dict, Any
from icecream import ic
from .inventory_service import reshape_product

ORDER_SERVICE_URL = "http://localhost:8007"

async def init_cart_session() -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{ORDER_SERVICE_URL}/cart/init")
            if response.status_code == 200:
                return response.json()
            return {"detail": "Failed to initialize cart session"}
    except Exception as e:
        ic(f"Error calling Order Service for cart init: {e}")
        return {"detail": f"Order Service communication error: {str(e)}"}

async def add_cart_item(data: dict) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{ORDER_SERVICE_URL}/cart/add", json=data)
            return response.json()
    except Exception as e:
        ic(f"Error adding item to cart: {e}")
        return {"detail": f"Order Service communication error: {str(e)}"}

async def remove_cart_item(data: dict) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{ORDER_SERVICE_URL}/cart/remove", json=data)
            return response.json()
    except Exception as e:
        ic(f"Error removing item from cart: {e}")
        return {"detail": f"Order Service communication error: {str(e)}"}

async def cancel_cart_session(data: dict) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{ORDER_SERVICE_URL}/cart/cancel", json=data)
            return response.json()
    except Exception as e:
        ic(f"Error cancelling cart: {e}")
        return {"detail": f"Order Service communication error: {str(e)}"}

async def get_cart_session(session_id: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ORDER_SERVICE_URL}/cart/{session_id}")
            if response.status_code == 200:
                data = response.json()
                # Reshape item_info inside each item
                payload = data.get("data") or {}
                items = payload.get("items") or []
                for item in items:
                    if "item_info" in item:
                        item["item_info"] = reshape_product(item["item_info"])
                return data
            return {"detail": "Cart session not found"}
    except Exception as e:
        ic(f"Error getting cart session: {e}")
        return {"detail": f"Order Service communication error: {str(e)}"}
