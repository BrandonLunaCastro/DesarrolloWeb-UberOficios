from fastapi import FastAPI
# Importamos el router que contiene nuestros endpoints
# de autenticación.
from app.routes.auth import router as auth_router
from app.routes.usuarios import router as usuarios_router
from app.routes.avisos import router as avisos_router
from app.routes.creditos import router as creditos_router
from fastapi.middleware.cors import CORSMiddleware

#crea una app Fast API
api = FastAPI()

# Incluimos el router de autenticación dentro de nuestra aplicación.
# Esto hace que FastAPI conozca los endpoints que definimos
# en routes/auth.py.
api.include_router(auth_router)
api.include_router(usuarios_router)
api.include_router(avisos_router)
api.include_router(creditos_router)

#cuando alguien haga una peticion get ejecuta nuestra funcion get

@api.get("/health")
def healt_check():
    return {"status" :  "ok"}


app = CORSMiddleware(
    app=api,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "https://uberoficios-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)