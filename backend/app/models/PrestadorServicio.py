from sqlalchemy import Column, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from app.database import Base


class PrestadorServicio(Base):
    __tablename__ = "prestador_servicio"

<<<<<<< HEAD
    id_prestador = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    matricula = Column(String(50), nullable=True)
    biografia = Column(Text, nullable=True)
    zona = Column(String(150), nullable=True)
    saldo_creditos = Column(
        Integer, nullable=False, server_default=text("0")
    )
=======
    id_prestador = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False, unique=True)
    telefono = Column(String, nullable=True)
    provincia = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
    zona = Column(String, nullable=True)
    oficio = Column(String, nullable=True)
    prom_calificacion = Column(Numeric(3, 2), nullable=True, default=0)
    creditos = Column(Integer, nullable=False, default=10)
    activo = Column(Boolean,nullable=False, default=True)
>>>>>>> 9ca3141 (feat(backend): reestructurar endpoints PUT /usuarios/perfil y POST /avisos)

    usuario = relationship("Usuario", back_populates="prestador")