from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class FotoPortafolio(Base):
    # Metadatos de una imagen guardada en almacenamiento externo.
    __tablename__ = "foto_portafolio"

    id_foto = Column(Integer, primary_key=True)
    id_prestador = Column(
        Integer,
        ForeignKey("prestador_servicio.id_prestador", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url_imagen = Column(String(2048), nullable=False)
    public_id = Column(String(255), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)

    prestador = relationship("PrestadorServicio", back_populates="fotos_portafolio")
