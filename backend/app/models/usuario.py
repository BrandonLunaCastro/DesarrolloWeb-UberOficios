from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True)
    id_rol = Column(
        Integer,
        ForeignKey("rol.id_rol", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)
    foto_perfil = Column(String(255), nullable=True)
    fecha_registro = Column(DateTime, nullable=False, server_default=func.now())

    rol = relationship("Rol", back_populates="usuarios")
    prestador = relationship(
        "PrestadorServicio",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )