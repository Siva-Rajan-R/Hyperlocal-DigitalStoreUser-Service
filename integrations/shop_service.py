import os
import httpx
from typing import Optional, List, Dict, Any
from icecream import ic

SHOP_SERVICE_URL = os.getenv("SHOP_SERVICE_URL", "http://127.0.0.1:8001")

def reshape_shop(shop: Any) -> Any:
    if isinstance(shop, list):
        return [reshape_shop(s) for s in shop]
    if not isinstance(shop, dict):
        return shop
    
    # Filter only customer-facing shop details
    s = {}
    allowed_keys = [
        "id", "name", "description", "tagline", "categories", 
        "banner_url", "logo_url", "operating_hours", 
        "delivery_options", "announcements", "address",
        "distance_km", "visibility_only", "is_ordering_enabled",
        "visible_online",
        "has_operating_hours", "has_delivery_options",
        "is_digital_store_configured", "can_show_digital_store_dashboard",
        "additional_infos", "datas"
    ]
    for key in allowed_keys:
        if key in shop:
            s[key] = shop[key]
            
    # Include category for schema compatibility if present
    if "category" in shop:
        s["category"] = shop["category"]
    elif "categories" in shop and shop["categories"]:
        s["category"] = shop["categories"][0]
    else:
        s["category"] = ""
        
    # Ensure visibility_only and is_ordering_enabled flags are consistently resolved
    add_infos = shop.get("additional_infos") or shop.get("datas") or {}
    vis_only = shop.get("visibility_only", add_infos.get("visibility_only", False))
    ord_enabled = shop.get("is_ordering_enabled", add_infos.get("is_ordering_enabled", not vis_only))
    if vis_only:
        ord_enabled = False
        
    s["visibility_only"] = bool(vis_only)
    s["is_ordering_enabled"] = bool(ord_enabled)
    
    hours = shop.get("operating_hours") or []
    deliv = shop.get("delivery_options") or []
    vis_online = bool(shop.get("visible_online", False))
    has_hours = len(hours) > 0
    has_deliv = len(deliv) > 0
    s["has_operating_hours"] = has_hours
    s["has_delivery_options"] = has_deliv
    s["is_digital_store_configured"] = bool(has_hours or has_deliv or vis_online)
    s["can_show_digital_store_dashboard"] = bool(has_hours or has_deliv or vis_online)
    
    if "distance_km" in shop:
        s["distance_km"] = shop["distance_km"]
    return s

async def get_shops(
    latitude: float,
    longitude: float,
    delivery_type: str = "INSTANT",
    limit: int = 10,
    offset: int = 1,
    timezone: str = "Asia/Kolkata"
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "latitude": latitude,
                "longitude": longitude,
                "delivery_type": delivery_type,
                "limit": limit,
                "offset": offset,
                "timezone": timezone
            }
            response = await client.post(
                f"{SHOP_SERVICE_URL}/shops/geofenced",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                raw_shops = data.get("data") if isinstance(data, dict) and "data" in data else data
                if isinstance(raw_shops, list):
                    return {"datas": [reshape_shop(s) for s in raw_shops]}
                elif isinstance(raw_shops, dict):
                    datas = raw_shops.get("datas") or []
                    if not datas and ("name" in raw_shops or "id" in raw_shops):
                        return {"datas": [reshape_shop(raw_shops)]}
                    return {"datas": [reshape_shop(s) for s in datas]}
            return {"datas": []}
    except Exception as e:
        ic(f"Error calling Shop Service geofenced endpoint: {e}")
        return {"datas": []}

async def get_shop_by_id(shop_id: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SHOP_SERVICE_URL}/shops/by/{shop_id}"
            )
            if response.status_code == 200:
                data = response.json()
                raw_shop = data.get("data") if isinstance(data, dict) and "data" in data else data
                return reshape_shop(raw_shop)
            return None
    except Exception as e:
        ic(f"Error calling Shop Service for shop {shop_id}: {e}")
        return None

