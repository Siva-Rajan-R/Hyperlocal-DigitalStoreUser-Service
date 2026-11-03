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
        "additional_infos", "datas", "vacation_mode", "vacation_infos"
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
    
    # Resolve vacation mode
    v_infos = shop.get("vacation_infos") or add_infos.get("vacation_infos") or {}
    vac_mode = shop.get("vacation_mode", add_infos.get("vacation_mode", v_infos.get("enabled", False) if isinstance(v_infos, dict) else False))
    s["vacation_mode"] = bool(vac_mode)
    s["vacation_infos"] = v_infos if isinstance(v_infos, dict) else {"enabled": bool(vac_mode)}
    
    mock_expired = os.getenv("MOCK_SUBSCRIPTION_EXPIRED", "false").lower() in ("true", "1", "yes")
    sub_status = shop.get("subscription_status") or add_infos.get("subscription_status") or ("expired" if mock_expired else "active")
    is_sub_expired = mock_expired or sub_status == "expired" or shop.get("is_subscription_expired", False)
    
    s["is_subscription_expired"] = bool(is_sub_expired)
    s["subscription_status"] = "expired" if is_sub_expired else "active"

    hours = shop.get("operating_hours") or []
    deliv = shop.get("delivery_options") or []
    vis_online = bool(shop.get("visible_online", False)) and not is_sub_expired
    has_hours = len(hours) > 0
    has_deliv = len(deliv) > 0
    s["has_operating_hours"] = has_hours
    s["has_delivery_options"] = has_deliv
    s["is_digital_store_configured"] = bool(has_hours or has_deliv or vis_online) and not is_sub_expired
    s["can_show_digital_store_dashboard"] = bool(has_hours or has_deliv or vis_online)
    if is_sub_expired:
        s["is_ordering_enabled"] = False
    
    if "distance_km" in shop:
        s["distance_km"] = shop["distance_km"]
    return s

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def filter_shop_delivery_by_location(shop: dict, user_lat: float, user_lon: float, target_delivery_type: Optional[str] = None) -> dict:
    if not shop:
        return shop
    shop_copy = dict(shop)
    address = shop_copy.get("address") or {}
    shop_lat_raw = address.get("latitude") if address.get("latitude") is not None else address.get("lat")
    shop_lon_raw = address.get("longitude") if address.get("longitude") is not None else address.get("lng")
    
    dist = None
    if shop_lat_raw is not None and shop_lon_raw is not None:
        try:
            dist = haversine(float(user_lat), float(user_lon), float(shop_lat_raw), float(shop_lon_raw))
            shop_copy["distance_km"] = round(dist, 2)
        except (ValueError, TypeError):
            dist = None

    if dist is None:
        # Distance unknown, preserve configured options
        return shop_copy

    default_radius_map = {
        "PICKUP_ONLY": 25.0,
        "INSTANT": 25.0,
        "STANDARD": 300.0,
        "NATIONWIDE": float('inf')
    }

    delivery_options = shop_copy.get("delivery_options") or []
    pickup_opt = None
    instant_opt = None
    standard_opt = None
    nationwide_opt = None

    for d in delivery_options:
        if not d or d.get("enabled") is False:
            continue
        raw_type = (d.get("type") or "").upper()
        if raw_type == "PICKUP_ONLY":
            pickup_opt = d
        elif raw_type in ("INSTANT", "EXPRESS"):
            instant_opt = d
        elif raw_type in ("STANDARD", "NORMAL"):
            standard_opt = d
        elif raw_type in ("NATIONWIDE", "SAME_DAY"):
            nationwide_opt = d

    def is_covered(opt, default_r):
        if not opt:
            return False
        if default_r == float('inf'):
            return True
        if dist is None:
            return False
        configured_r = None
        raw_r = opt.get("radius")
        if raw_r is not None:
            try:
                r = float(raw_r)
                if r > 0:
                    configured_r = r
            except (ValueError, TypeError):
                pass
        max_r = configured_r if configured_r is not None else default_r
        return dist <= max_r

    pickup_covered = is_covered(pickup_opt, default_radius_map.get("PICKUP_ONLY", 25.0))
    instant_covered = is_covered(instant_opt, default_radius_map.get("INSTANT", 25.0))
    standard_covered = is_covered(standard_opt, default_radius_map.get("STANDARD", 300.0))
    nationwide_covered = is_covered(nationwide_opt, float('inf'))

    acceptable_options = []
    if pickup_covered:
        acceptable_options.append(pickup_opt)

    # Hierarchical home delivery selection:
    # If near and covered by Instant: accept ONLY Instant (Standard/Nationwide suppressed for this near location)
    # Else if covered by Standard: accept Standard
    # Else if covered by Nationwide: accept Nationwide
    if instant_covered:
        acceptable_options.append(instant_opt)
    elif standard_covered:
        acceptable_options.append(standard_opt)
    elif nationwide_covered:
        acceptable_options.append(nationwide_opt)

    if target_delivery_type:
        t_upper = target_delivery_type.upper()
        acceptable_options = [
            opt for opt in acceptable_options
            if (opt.get("type") or "").upper() == t_upper or
               (t_upper == "INSTANT" and (opt.get("type") or "").upper() == "EXPRESS") or
               (t_upper == "STANDARD" and (opt.get("type") or "").upper() == "NORMAL") or
               (t_upper == "NATIONWIDE" and (opt.get("type") or "").upper() == "SAME_DAY")
        ]

    shop_copy["delivery_options"] = acceptable_options
    return shop_copy

async def get_shops(
    latitude: float,
    longitude: float,
    delivery_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 1,
    timezone: str = "Asia/Kolkata"
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "latitude": latitude,
                "longitude": longitude,
                "limit": limit,
                "offset": offset,
                "timezone": timezone
            }
            if delivery_type:
                payload["delivery_type"] = delivery_type
            response = await client.post(
                f"{SHOP_SERVICE_URL}/shops/geofenced",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                raw_shops = data.get("data") if isinstance(data, dict) and "data" in data else data
                if isinstance(raw_shops, list):
                    return {"datas": [reshape_shop(filter_shop_delivery_by_location(s, latitude, longitude, delivery_type)) for s in raw_shops if s and s.get("visible_online") is True]}
                elif isinstance(raw_shops, dict):
                    datas = raw_shops.get("datas") or []
                    if not datas and ("name" in raw_shops or "id" in raw_shops):
                        if raw_shops.get("visible_online") is True:
                            return {"datas": [reshape_shop(filter_shop_delivery_by_location(raw_shops, latitude, longitude, delivery_type))]}
                        return {"datas": []}
                    return {"datas": [reshape_shop(filter_shop_delivery_by_location(s, latitude, longitude, delivery_type)) for s in datas if s and s.get("visible_online") is True]}
            return {"datas": []}
    except Exception as e:
        ic(f"Error calling Shop Service geofenced endpoint: {e}")
        return {"datas": []}

async def get_shop_by_id(
    shop_id: str,
    allow_offline: bool = False,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SHOP_SERVICE_URL}/shops/by/{shop_id}"
            )
            if response.status_code == 200:
                data = response.json()
                raw_shop = data.get("data") if isinstance(data, dict) and "data" in data else data
                if not raw_shop:
                    return None
                # If shop is not visible online, do not send to digital store response
                if not allow_offline and not raw_shop.get("visible_online"):
                    return None
                if latitude is not None and longitude is not None:
                    raw_shop = filter_shop_delivery_by_location(raw_shop, latitude, longitude)
                return reshape_shop(raw_shop)
            return None
    except Exception as e:
        ic(f"Error calling Shop Service for shop {shop_id}: {e}")
        return None

