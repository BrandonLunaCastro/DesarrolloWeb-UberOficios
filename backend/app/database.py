from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

#le decimos al sistema que cargue las variables dentro de nuestro archivo env
load_dotenv()

#esta linea de codigo sirve para leer nuestra variable de entorno que es la que actualmente contiene nuestra coneccion a la base de datos 
DATABASE_URL = os.getenv("DATABASE_URL")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "3"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "1"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

#basicamente creamos el puente entre nuestra base de datos y el programa 
engine = create_engine(
    DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=1800,
)

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
        db.close()