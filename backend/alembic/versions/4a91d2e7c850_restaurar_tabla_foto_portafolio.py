"""restaurar tabla foto_portafolio

Revision ID: 4a91d2e7c850
Revises: f7a6c2d913e4, f16b8c4d2e71
Create Date: 2026-11-20 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4a91d2e7c850"
down_revision: Union[str, Sequence[str], None] = (
    "f7a6c2d913e4",
    "f16b8c4d2e71",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "foto_portafolio",
        sa.Column("id_foto", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_prestador", sa.Integer(), nullable=False),
        sa.Column("url_imagen", sa.String(length=2048), nullable=False),
        sa.Column("public_id", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["id_prestador"],
            ["prestador_servicio.id_prestador"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id_foto"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        op.f("ix_foto_portafolio_id_prestador"),
        "foto_portafolio",
        ["id_prestador"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_foto_portafolio_id_prestador"),
        table_name="foto_portafolio",
    )
    op.drop_table("foto_portafolio")
