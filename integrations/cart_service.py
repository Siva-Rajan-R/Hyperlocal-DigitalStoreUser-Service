import os
import httpx
from typing import Optional, Dict, Any
from icecream import ic
from dotenv import load_dotenv
from .inventory_service import reshape_product
load_dotenv()

from fastapi import HTTPException
from .shop_service import get_shop_by_id

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8007")

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
    # Check if shop is visibility only
    shop_id = data.get("shop_id")
    if shop_id:
        shop = await get_shop_by_id(shop_id)
        if shop and (shop.get("visibility_only") is True or shop.get("is_ordering_enabled") is False):
            shop_name = shop.get("name", shop_id)
            raise HTTPException(
                status_code=400,
                detail=f"Online ordering is not available for shop '{shop_name}'. This shop is listed for visibility only."
            )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{ORDER_SERVICE_URL}/cart/add", json=data)
            if response.status_code >= 400:
                try:
                    err_json = response.json()
                    err_detail = err_json.get("detail", response.text)
                except Exception:
                    err_detail = response.text
                raise HTTPException(status_code=response.status_code, detail=err_detail)
            return response.json()
    except HTTPException:
        raise
    except Exception as e:
        ic(f"Error adding item to cart: {e}")
        raise HTTPException(status_code=500, detail=f"Order Service communication error: {str(e)}")

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
