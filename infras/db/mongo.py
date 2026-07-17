from motor.motor_asyncio import AsyncIOMotorClient
from core.configs.settings_config import SETTINGS

class MongoDBManager:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        cls.client = AsyncIOMotorClient(SETTINGS.MONGO_URL)
        cls.db = cls.client[SETTINGS.MONGO_DB_NAME]
        
        # Ensure Indexes
        await cls.db.users.create_index("user_id", unique=True)
        await cls.db.search_histories.create_index([("user_id", 1), ("timestamp", -1)])
        await cls.db.search_histories.create_index([("user_id", 1), ("search_term", 1)], unique=True)
        await cls.db.favourite_products.create_index([("user_id", 1), ("product_id", 1)], unique=True)
        await cls.db.favourite_shops.create_index([("user_id", 1), ("shop_id", 1)], unique=True)
        await cls.db.reviews.create_index([("user_id", 1), ("shop_id", 1)], unique=True)
        await cls.db.reviews.create_index("shop_id")
        await cls.db.user_orders.create_index("order_id", unique=True)
        await cls.db.user_orders.create_index("user_id")

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()

def get_collection(name: str):
    return MongoDBManager.db[name]
