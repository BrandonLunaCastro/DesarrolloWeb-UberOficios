from sqlalchemy import Column, Integer , String 
from sqlalchemy.orm import relationship
from app.database import Base

class Usuario(Base):
    __tablename__="usuario"
    
    id_usuario=Column(Integer, primary_key=True,index=True)
    nombre_apellido=Column(String, nullable=False)
    correo=Column(String, unique=True,nullable=False, index=True)
    contrasena=Column(String, nullable=False)
    estado=Column(String, nullable=False,default="activo")
    
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)
    prestador = relationship("PrestadorServicio", back_populates="usuario", uselist=False)