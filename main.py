import logging
from contextlib import asynccontextmanager

import dotenv
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from rate_limiter import limiter
from events import views as events_views
from users import views as users_views

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.DEBUG)
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://localhost:8000",
    "http://localhost:8003",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(events_views.router)
app.include_router(users_views.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
