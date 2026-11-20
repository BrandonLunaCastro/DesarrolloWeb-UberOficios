"""aviso vencimiento, foto de calificacion y notificacion pendiente

Revision ID: 5b8d2a7f1c40
Revises: 4a91d2e7c850
Create Date: 2026-11-20 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b8d2a7f1c40"
down_revision: Union[str, Sequence[str], None] = "4a91d2e7c850"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE estado_aviso_enum ADD VALUE IF NOT EXISTS 'EXPIRADO'")
    op.add_column(
        "calificacion",
        sa.Column("url_comprobante", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "calificacion",
        sa.Column("public_id_comprobante", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notificacion",
        sa.Column("id_postulacion", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_notificacion_postulacion",
        "notificacion",
        "postulacion",
        ["id_postulacion"],
        ["id_postulacion"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_notificacion_id_postulacion",
        "notificacion",
        ["id_postulacion"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO notificacion
            (id_usuario, id_postulacion, tipo, mensaje, leida)
        SELECT
            aviso.id_cliente,
            postulacion.id_postulacion,
            'calificacion_pendiente',
            'Calificá el trabajo realizado para "' || aviso.titulo || '".',
            FALSE
        FROM postulacion
        JOIN aviso ON aviso.id_aviso = postulacion.id_aviso
        LEFT JOIN calificacion
            ON calificacion.id_postulacion = postulacion.id_postulacion
        WHERE aviso.estado = 'FINALIZADO'
          AND postulacion.estado = 'ACEPTADO'
          AND calificacion.id_calificacion IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM notificacion
              WHERE notificacion.id_postulacion = postulacion.id_postulacion
                AND notificacion.tipo = 'calificacion_pendiente'
          )
        """
    )


def downgrade() -> None:
    op.execute(
        "UPDATE aviso SET estado = 'ABIERTO' WHERE estado = 'EXPIRADO'"
    )
    op.drop_index("ix_notificacion_id_postulacion", table_name="notificacion")
    op.drop_constraint(
        "fk_notificacion_postulacion",
        "notificacion",
        type_="foreignkey",
    )
    op.drop_column("notificacion", "id_postulacion")
    op.drop_column("calificacion", "public_id_comprobante")
    op.drop_column("calificacion", "url_comprobante")
