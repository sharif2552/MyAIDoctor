from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import auth, chat, health, reports, sessions
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine

app = FastAPI(title=settings.app_name)

_origins_raw = [x.strip() for x in settings.cors_allow_origins.split(",") if x.strip()]
_allow_all_origins = any(x == "*" for x in _origins_raw)
_allow_origins = [x for x in _origins_raw if x != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all_origins else _allow_origins,
    # Note: browsers reject credentialed requests when Access-Control-Allow-Origin is '*'
    allow_credentials=False if _allow_all_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.options('/{rest_of_path:path}')
def preflight_handler(rest_of_path: str):
    return Response(status_code=200)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(reports.router)
