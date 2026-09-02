import os
import httpx
from typing import Optional, List, Dict, Any
from icecream import ic

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8004")

def reshape_product(prod: Any) -> Any:
    if isinstance(prod, list):
        return [reshape_product(p) for p in prod]
    if not isinstance(prod, dict):
        return prod
    
    p = dict(prod)
    p.pop("buy_price", None)
    p.pop("reorder_point_infos", None)
    p.pop("storage_location_infos", None)
    
    if "pricing_infos" in p and isinstance(p["pricing_infos"], dict):
        p["pricing_infos"].pop("buy_price", None)
        
    if "variants" in p:
        if isinstance(p["variants"], dict):
            p["variants"] = {k: reshape_product(v) for k, v in p["variants"].items()}
        elif isinstance(p["variants"], list):
            p["variants"] = [reshape_product(v) for v in p["variants"]]
            
    return p

async def get_products(query: str = "", limit: int = 10, offset: int = 1) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{INVENTORY_SERVICE_URL}/inventories",
                params={"q": query, "limit": limit, "offset": offset, "visible_online": True}
            )
            if response.status_code == 200:
                data = response.json()
                raw_prods = data.get("data") if isinstance(data, dict) and "data" in data else data
                # If list of products
                if isinstance(raw_prods, list):
                    return {"datas": [reshape_product(p) for p in raw_prods]}
                elif isinstance(raw_prods, dict):
                    datas = raw_prods.get("datas") or []
                    return {"datas": [reshape_product(p) for p in datas]}
            return {"datas": []}
    except Exception as e:
        ic(f"Error calling Inventory Service: {e}")
        return {"datas": []}

async def get_products_by_shop(shop_id: str, query: str = "", limit: int = 10, offset: int = 1) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{INVENTORY_SERVICE_URL}/inventories/by/shop/{shop_id}",
                params={"q": query, "limit": limit, "offset": offset, "visible_online": True}
            )
            if response.status_code == 200:
                data = response.json()
                raw_prods = data.get("data") if isinstance(data, dict) and "data" in data else data
                # If list of products
                if isinstance(raw_prods, list):
                    return {"datas": [reshape_product(p) for p in raw_prods]}
                elif isinstance(raw_prods, dict):
                    datas = raw_prods.get("datas") or []
                    return {"datas": [reshape_product(p) for p in datas]}
            return {"datas": []}
    except Exception as e:
        ic(f"Error calling Inventory Service for shop {shop_id}: {e}")
        return {"datas": []}

async def get_product_by_id(shop_id: str, product_id: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{INVENTORY_SERVICE_URL}/inventories/by/id/{shop_id}/{product_id}"
            )
            if response.status_code == 200:
                data = response.json()
                raw_prod = data.get("data") if isinstance(data, dict) and "data" in data else data
                if isinstance(raw_prod, dict):
                    if raw_prod.get("visible_online") is False:
                        return None
                    return reshape_product(raw_prod)
            return None
    except Exception as e:
        ic(f"Error calling Inventory Service for product {product_id}: {e}")
        return None
