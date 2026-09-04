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
        "delivery_options", "announcements", "address"
    ]
    for key in allowed_keys:
        if key in shop:
            s[key] = shop[key]
            
    # Include category for schema compatibility if present
    if "category" in shop:
        s["category"] = shop["category"]
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
                return reshape_shop(response.json())
            return None
    except Exception as e:
        ic(f"Error calling Shop Service for shop {shop_id}: {e}")
        return None

