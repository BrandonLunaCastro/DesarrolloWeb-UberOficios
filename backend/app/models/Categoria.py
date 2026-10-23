from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Categoria(Base):
    __tablename__ = "categoria"

    id_categoria = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)

    avisos = relationship("Aviso", back_populates="categoria")
