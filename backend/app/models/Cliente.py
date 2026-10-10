from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=False,
        unique=True,
    )
    zona = Column(String, nullable=True)
    telefono = Column(String, nullable=True)

    avisos = relationship("Aviso", back_populates="cliente")
