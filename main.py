import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routers.v1 import user_routes, digitalstore_routes
from infras.db.mongo import MongoDBManager
from core.configs.settings_config import SETTINGS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await MongoDBManager.connect()
    yield
    # Shutdown: Close connections
    await MongoDBManager.disconnect()

app = FastAPI(
    title="Digital Store User Service",
    description="Microservice managing user profiles, search histories, favorites, reviews, orders and payment receipts via MongoDB",
    lifespan=lifespan
)

app.include_router(user_routes.router)
app.include_router(digitalstore_routes.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=SETTINGS.PORT, reload=True)
