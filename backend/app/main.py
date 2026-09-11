from fastapi import FastAPI
# Importamos el router que contiene nuestros endpoints
# de autenticación.
from app.routes.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware


#crea una app Fast API
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos el router de autenticación dentro de nuestra aplicación.
# Esto hace que FastAPI conozca los endpoints que definimos
# en routes/auth.py.
app.include_router(auth_router)


#cuando alguien haga una peticion get ejecuta nuestra funcion get

@app.get("/health")
def healt_check():
    return {"status" :  "ok"}
