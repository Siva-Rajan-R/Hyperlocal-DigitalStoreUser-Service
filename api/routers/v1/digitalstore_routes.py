from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
from integrations.inventory_service import get_products, get_product_by_id
from integrations.shop_service import get_shops, get_shop_by_id
from integrations.order_service import get_orders_by_user_id, get_order_by_id
from integrations.cart_service import init_cart_session, add_cart_item, remove_cart_item, cancel_cart_session, get_cart_session

router = APIRouter(
    prefix="/digitalstore",
    tags=["DigitalStore Aggregated Operations"]
)

# --- PRODUCTS ---
@router.get("/products")
async def fetch_products(
    q: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=1, ge=1)
):
    return await get_products(query=q, limit=limit, offset=offset)

@router.get("/products/{shop_id}/{id}")
async def fetch_product_by_id(shop_id: str, id: str):
    product = await get_product_by_id(shop_id=shop_id, product_id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- SHOPS ---
@router.get("/shops")
async def fetch_shops(
    q: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=1, ge=1)
):
    return await get_shops(query=q, limit=limit, offset=offset)

@router.get("/shops/{shop_id}")
async def fetch_shop_by_id(shop_id: str):
    shop = await get_shop_by_id(shop_id=shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

# --- ORDERS ---
@router.get("/orders/by/user/{user_id}")
async def fetch_user_orders(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=1, ge=1)
):
    return await get_orders_by_user_id(user_id=user_id, limit=limit, offset=offset)

@router.get("/orders/{shop_id}/{id}")
async def fetch_order_by_id(shop_id: str, id: str):
    order = await get_order_by_id(shop_id=shop_id, order_id=id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# --- CART ---
@router.post("/cart/init")
async def init_cart():
    return await init_cart_session()

@router.post("/cart/add")
async def add_item(request: Request):
    data = await request.json()
    return await add_cart_item(data)

@router.post("/cart/remove")
async def remove_item(request: Request):
    data = await request.json()
    return await remove_cart_item(data)

@router.post("/cart/cancel")
async def cancel_cart(request: Request):
    data = await request.json()
    return await cancel_cart_session(data)

@router.get("/cart/{session_id}")
async def get_cart(session_id: str):
    return await get_cart_session(session_id)
