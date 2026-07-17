from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AddressModel(BaseModel):
    address_id: Optional[str] = None
    phone: str
    full_address: str
    city: str
    pincode: str
    state: str
    is_default: Optional[bool] = False

class UserProfileSchema(BaseModel):
    user_id: str
    name: str
    addresses: List[AddressModel] = []
    preferences: Dict[str, Any] = {}

class UpdateUserProfileSchema(BaseModel):
    name: Optional[str] = None
    addresses: Optional[List[AddressModel]] = None
    preferences: Optional[Dict[str, Any]] = None

class SearchHistorySchema(BaseModel):
    user_id: str
    search_term: str

class FavoriteProductSchema(BaseModel):
    user_id: str
    product_id: str

class FavoriteShopSchema(BaseModel):
    user_id: str
    shop_id: str

class ShopReviewSchema(BaseModel):
    user_id: str
    shop_id: str
    rating: float = Field(..., ge=1.0, le=5.0)
    review_text: Optional[str] = None

class PaymentInfoSchema(BaseModel):
    transaction_id: str
    provider: str  # e.g., 'payu', 'cashfree'
    amount: float

class UserOrderSchema(BaseModel):
    user_id: str
    order_id: str
    payment_info: Optional[PaymentInfoSchema] = None
