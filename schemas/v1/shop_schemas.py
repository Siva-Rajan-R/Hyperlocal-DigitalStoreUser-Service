from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class DeliveryTypeEnum(str, Enum):
    PICKUP_ONLY = "PICKUP_ONLY"
    INSTANT = "INSTANT"
    STANDARD = "STANDARD"
    NATIONWIDE = "NATIONWIDE"

class GeofencedShopRequestSchema(BaseModel):
    latitude: float = Field(..., description="User latitude")
    longitude: float = Field(..., description="User longitude")
    delivery_type: DeliveryTypeEnum = Field(default=DeliveryTypeEnum.INSTANT, description="Delivery type")
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    offset: Optional[int] = Field(default=1, ge=1)
    timezone: Optional[str] = Field(default="Asia/Kolkata")
