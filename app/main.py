from fastapi import FastAPI

#crea una app Fast API
app = FastAPI()

#cuando alguien haga una peticion get ejecuta nuestra funcion get

@app.get("/health")
def healt_check():
    return {"status" :  "ok"}