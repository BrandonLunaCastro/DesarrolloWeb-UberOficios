from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

#le decimos al sistema que cargue las variables dentro de nuestro archivo env
load_dotenv()

#esta linea de codigo sirve para leer nuestra variable de entorno que es la que actualmente contiene nuestra coneccion a la base de datos 
DATABASE_URL = os.getenv("DATABASE_URL")

#basicamente creamos el puente entre nuestra base de datos y el programa 
engine = create_engine(DATABASE_URL)

# esto nos permite crear sesiones, las cuales son importantes al momento que interactuen en la base de datos 
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush= False,
    bind = engine 
)

Base = declarative_base()

#cuando consultamos la base de datos esta funcion se encarga de cerrarla 
def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close