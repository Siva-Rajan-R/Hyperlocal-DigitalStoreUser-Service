from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
from infras.db.mongo import get_collection
from schemas.v1.user_schemas import (
    UserProfileSchema,
    UpdateUserProfileSchema,
    SearchHistorySchema,
    FavoriteProductSchema,
    FavoriteShopSchema,
    ShopReviewSchema,
    UserOrderSchema
)

router = APIRouter(
    prefix="/digitalstore/users",
    tags=["DigitalStore User Operations"]
)

# --- PROFILE ENDPOINTS ---
@router.post("/profile", status_code=status.HTTP_201_CREATED)
async def create_profile(profile: UserProfileSchema):
    import uuid
    users = get_collection("users")
    
    addresses = []
    for addr in profile.addresses:
        addr_dict = addr.model_dump()
        if not addr_dict.get("address_id"):
            addr_dict["address_id"] = str(uuid.uuid4())
        addresses.append(addr_dict)

    existing = await users.find_one({"user_id": profile.user_id})
    if existing:
        await users.update_one(
            {"user_id": profile.user_id},
            {"$set": {
                "name": profile.name,
                "addresses": addresses,
                "preferences": profile.preferences,
                "updated_at": datetime.utcnow()
            }}
        )
        return {"message": "Profile updated successfully", "user_id": profile.user_id}
    
    await users.insert_one({
        "user_id": profile.user_id,
        "name": profile.name,
        "addresses": addresses,
        "preferences": profile.preferences,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    return {"message": "Profile created successfully", "user_id": profile.user_id}

@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    users = get_collection("users")
    profile = await users.find_one({"user_id": user_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile

@router.put("/profile/{user_id}")
async def update_profile(user_id: str, data: UpdateUserProfileSchema):
    import uuid
    users = get_collection("users")
    existing = await users.find_one({"user_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.addresses is not None:
        addresses = []
        for addr in data.addresses:
            addr_dict = addr.model_dump()
            if not addr_dict.get("address_id"):
                addr_dict["address_id"] = str(uuid.uuid4())
            addresses.append(addr_dict)
        update_data["addresses"] = addresses
    if data.preferences is not None:
        update_data["preferences"] = data.preferences
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await users.update_one({"user_id": user_id}, {"$set": update_data})
        
    return {"message": "Profile updated successfully", "user_id": user_id}

@router.get("/{user_id}/address/{address_id}")
async def get_user_address(user_id: str, address_id: str):
    users = get_collection("users")
    user = await users.find_one(
        {"user_id": user_id, "addresses.address_id": address_id},
        {"addresses.$": 1, "_id": 0}
    )
    if not user or not user.get("addresses"):
        raise HTTPException(status_code=404, detail="Address not found")
    return user["addresses"][0]


# --- SEARCH HISTORY ENDPOINTS ---
@router.post("/search")
async def add_search_history(data: SearchHistorySchema):
    histories = get_collection("search_histories")
    await histories.update_one(
        {"user_id": data.user_id, "search_term": data.search_term},
        {
            "$setOnInsert": {"created_at": datetime.utcnow()},
            "$set": {"timestamp": datetime.utcnow()},
            "$inc": {"count": 1}
        },
        upsert=True
    )
    return {"message": "Search history saved"}

@router.get("/search/{user_id}")
async def get_search_history(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    histories = get_collection("search_histories")
    cursor = histories.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
    results = await cursor.to_list(length=limit)
    return results

@router.delete("/search/{user_id}")
async def clear_search_history(user_id: str):
    histories = get_collection("search_histories")
    await histories.delete_many({"user_id": user_id})
    return {"message": "Search history cleared"}


# --- FAVORITES ENDPOINTS ---
@router.post("/favorites/product")
async def favorite_product(data: FavoriteProductSchema):
    favs = get_collection("favourite_products")
    await favs.update_one(
        {"user_id": data.user_id, "product_id": data.product_id},
        {"$set": {"timestamp": datetime.utcnow()}},
        upsert=True
    )
    return {"message": "Product favorited"}

@router.delete("/favorites/product/{user_id}/{product_id}")
async def unfavorite_product(user_id: str, product_id: str):
    favs = get_collection("favourite_products")
    result = await favs.delete_one({"user_id": user_id, "product_id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite product not found")
    return {"message": "Product unfavorited"}

@router.get("/favorites/products/{user_id}")
async def get_favorite_products(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    favs = get_collection("favourite_products")
    cursor = favs.find({"user_id": user_id}, {"_id": 0, "product_id": 1}).skip(offset).limit(limit)
    results = await cursor.to_list(length=limit)
    return [r["product_id"] for r in results]

@router.post("/favorites/shop")
async def favorite_shop(data: FavoriteShopSchema):
    favs = get_collection("favourite_shops")
    await favs.update_one(
        {"user_id": data.user_id, "shop_id": data.shop_id},
        {"$set": {"timestamp": datetime.utcnow()}},
        upsert=True
    )
    return {"message": "Shop followed/favorited"}

@router.delete("/favorites/shop/{user_id}/{shop_id}")
async def unfavorite_shop(user_id: str, shop_id: str):
    favs = get_collection("favourite_shops")
    result = await favs.delete_one({"user_id": user_id, "shop_id": shop_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite shop/follow not found")
    return {"message": "Shop unfollowed/unfavorited"}

@router.get("/favorites/shops/{user_id}")
async def get_favorite_shops(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    favs = get_collection("favourite_shops")
    cursor = favs.find({"user_id": user_id}, {"_id": 0, "shop_id": 1}).skip(offset).limit(limit)
    results = await cursor.to_list(length=limit)
    return [r["shop_id"] for r in results]


# --- REVIEWS ENDPOINTS ---
@router.post("/reviews")
async def review_shop(data: ShopReviewSchema):
    reviews = get_collection("reviews")
    await reviews.update_one(
        {"user_id": data.user_id, "shop_id": data.shop_id},
        {"$set": {
            "rating": data.rating,
            "review_text": data.review_text,
            "timestamp": datetime.utcnow()
        }},
        upsert=True
    )
    return {"message": "Shop review saved"}

@router.get("/reviews/shop/{shop_id}")
async def get_shop_reviews(
    shop_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    reviews = get_collection("reviews")
    cursor = reviews.find({"shop_id": shop_id}, {"_id": 0}).skip(offset).limit(limit)
    results = await cursor.to_list(length=limit)
    return results

@router.get("/reviews/user/{user_id}")
async def get_user_reviews(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    reviews = get_collection("reviews")
    cursor = reviews.find({"user_id": user_id}, {"_id": 0}).skip(offset).limit(limit)
    results = await cursor.to_list(length=limit)
    return results


# --- ORDERS & PAYMENTS ENDPOINTS ---
@router.post("/orders")
async def link_order_payment(data: UserOrderSchema):
    orders = get_collection("user_orders")
    payload = {
        "user_id": data.user_id,
        "order_id": data.order_id,
        "timestamp": datetime.utcnow()
    }
    if data.payment_info:
        payload["payment_info"] = data.payment_info.model_dump()
        
    await orders.update_one(
        {"order_id": data.order_id},
        {"$set": payload},
        upsert=True
    )
    return {"message": "Order mapped and saved successfully"}

@router.get("/orders/{user_id}")
async def get_user_orders(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    orders = get_collection("user_orders")
    cursor = orders.find({"user_id": user_id}, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
    results = await cursor.to_list(length=limit)
    return results

@router.post("/orders/bulk")
async def get_bulk_orders(order_ids: List[str]):
    orders = get_collection("user_orders")
    cursor = orders.find({"order_id": {"$in": order_ids}}, {"_id": 0})
    results = await cursor.to_list(length=len(order_ids))
    return results
