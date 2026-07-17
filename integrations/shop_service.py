import httpx
from typing import Optional, List, Dict, Any
from icecream import ic

SHOP_SERVICE_URL = "http://localhost:8001"

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
        "delivery_options", "announcements"
    ]
    for key in allowed_keys:
        if key in shop:
            s[key] = shop[key]
            
    # Include category for schema compatibility if present
    if "category" in shop:
        s["category"] = shop["category"]
    return s

async def get_shops(query: str = "", limit: int = 10, offset: int = 1) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SHOP_SERVICE_URL}/shops",
                params={"q": query, "limit": limit, "offset": offset}
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return {"datas": [reshape_shop(s) for s in data]}
                elif isinstance(data, dict):
                    datas = data.get("datas") or []
                    # check if it is direct array or pagination dict
                    if not datas and "name" in data: # single object or raw array returned directly
                        return {"datas": [reshape_shop(data)]}
                    data["datas"] = [reshape_shop(s) for s in datas]
                    return data
            return {"datas": []}
    except Exception as e:
        ic(f"Error calling Shop Service: {e}")
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
