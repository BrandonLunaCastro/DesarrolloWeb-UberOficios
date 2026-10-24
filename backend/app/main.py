from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.usuarios import router as usuarios_router
from app.routes.avisos import router as avisos_router
from app.routes.creditos import router as creditos_router
from app.routes.chat import router as chat_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://uberoficios-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(avisos_router)
app.include_router(creditos_router)
app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
