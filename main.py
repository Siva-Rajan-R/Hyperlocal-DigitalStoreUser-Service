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










# --- INJECTED LOGGING SETUP ---
import time
import logging
import traceback
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# ANSI Escape Codes for Colors
RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    request.state.error_detail = str(exc.detail)
    logger.error(f"{RED}❌ HTTP {exc.status_code} Error on {request.method} {request.url.path}:{RESET} {exc.detail}")
    
    if isinstance(exc.detail, dict) and "msg" in exc.detail:
        exc.detail["status_type"] = exc.detail.get("status_type", "error")
        exc.detail["title"] = exc.detail.get("title", "HTTP Error")
        exc.detail["description"] = exc.detail.get("description", exc.detail.get("msg", str(exc.detail)))
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "msg": "HTTP Error",
                "status_code": exc.status_code,
                "success": False,
                "status_type": "error",
                "title": "HTTP Error",
                "description": str(exc.detail)
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = str(exc.errors())
    request.state.error_detail = error_details
    logger.error(f"{RED}❌ Validation Error on {request.method} {request.url.path}:{RESET} {error_details}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "msg": "Validation Error",
                "status_code": 422,
                "success": False,
                "status_type": "error",
                "title": "Validation Error",
                "description": error_details
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_details = str(exc)
    request.state.error_detail = error_details
    logger.error(f"{RED}❌ Unhandled Exception on {request.method} {request.url.path}:{RESET} {error_details}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "msg": "Internal Server Error",
                "status_code": 500,
                "success": False,
                "status_type": "error",
                "title": "System Error",
                "description": error_details
            }
        }
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    if request.method == "GET":
        method_color = CYAN
    elif request.method == "POST":
        method_color = GREEN
    elif request.method == "PUT":
        method_color = YELLOW
    elif request.method == "DELETE":
        method_color = RED
    else:
        method_color = MAGENTA
    
    logger.info(f"{BLUE}▶ Incoming:{RESET} {method_color}{request.method}{RESET} {request.url.path}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        raise e
        
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}ms"
    
    if response.status_code < 300:
        status_color = GREEN
    elif response.status_code < 400:
        status_color = YELLOW
    else:
        status_color = RED
        
    error_msg = ""
    if response.status_code >= 400 and hasattr(request.state, "error_detail"):
        error_msg = f" - {RED}Error: {request.state.error_detail}{RESET}"
        
    logger.info(f"{MAGENTA}✔ Completed:{RESET} {method_color}{request.method}{RESET} {request.url.path} - {status_color}Status: {response.status_code}{RESET} - {YELLOW}Time: {formatted_process_time}{RESET}{error_msg}")
    
    return response
# ------------------------------


# --- INJECTED USER CONTEXT MIDDLEWARE ---
import json
from fastapi import Request
from core.utils.user_context import current_user_ctx

@app.middleware("http")
async def user_context_middleware(request: Request, call_next):
    user_infos_header = request.headers.get("x-user-infos")
    if user_infos_header:
        try:
            user_infos = json.loads(user_infos_header)
            current_user_ctx.set(user_infos)
        except Exception:
            pass
    return await call_next(request)
# ----------------------------------------
