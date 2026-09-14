import os
import httpx
from typing import Optional, List, Dict, Any
from icecream import ic

from fastapi import HTTPException
from .shop_service import get_shop_by_id

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8007")

def reshape_order(order: Any) -> Any:
    if isinstance(order, list):
        return [reshape_order(o) for o in order]
    if not isinstance(order, dict):
        return order
    
    o = dict(order)
    # Strip sensitive cost information
    if "item_infos" in o and isinstance(o["item_infos"], dict):
        o["item_infos"].pop("total_order_cost", None)
        
    if "items" in o and isinstance(o["items"], list):
        new_items = []
        for item in o["items"]:
            if isinstance(item, dict):
                item_copy = dict(item)
                item_copy.pop("buy_price", None)
                new_items.append(item_copy)
            else:
                new_items.append(item)
        o["items"] = new_items
        
    return o

async def create_order(data: dict) -> Dict[str, Any]:
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
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{ORDER_SERVICE_URL}/orders",
                json=data
            )
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
        ic(f"Error calling Order Service for creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Order Service communication error: {str(e)}")

async def get_orders_by_user_id(user_id: str, limit: int = 10, offset: int = 1) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ORDER_SERVICE_URL}/orders/by/user/{user_id}",
                params={"limit": limit, "offset": offset}
            )
            if response.status_code == 200:
                data = response.json()
                # Check response wrapper
                payload = data.get("data") if isinstance(data, dict) and "data" in data else data
                if isinstance(payload, list):
                    return {"datas": [reshape_order(o) for o in payload]}
                elif isinstance(payload, dict):
                    datas = payload.get("datas") or []
                    payload["datas"] = [reshape_order(o) for o in datas]
                    return payload
            return {"datas": []}
    except Exception as e:
        ic(f"Error calling Order Service: {e}")
        return {"datas": []}

async def get_order_by_id(shop_id: str, order_id: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ORDER_SERVICE_URL}/orders/{shop_id}/{order_id}"
            )
            if response.status_code == 200:
                data = response.json()
                payload = data.get("data") if isinstance(data, dict) and "data" in data else data
                return reshape_order(payload)
            return None
    except Exception as e:
        ic(f"Error calling Order Service for order {order_id}: {e}")
        return None
