from sqlalchemy import Column, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from app.database import Base


class PrestadorServicio(Base):
    __tablename__ = "prestador_servicio"

    id_prestador = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    matricula = Column(String(50), nullable=True)
    biografia = Column(Text, nullable=True)
    radio_cobertura_km = Column(
        Integer, nullable=True, server_default=text("10")
    )
    saldo_creditos = Column(
        Integer, nullable=False, server_default=text("0")
    )

    usuario = relationship("Usuario", back_populates="prestador")