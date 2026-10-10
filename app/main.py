
# ============================================================
# FASTAPI MAIN
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.auth import router as auth_router
from app.api.movies import router as movies_router


# ============================================================
# CREATE APP
# ============================================================

app = FastAPI(
    title="Movie AI Assistant",
    description="AI Movie Recommendation Assistant",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(movies_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/api")
def api_status():
    return {
        "success": True,
        "message": "Movie AI Assistant API is running.",
    }


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True,
    ),
    name="frontend",
)