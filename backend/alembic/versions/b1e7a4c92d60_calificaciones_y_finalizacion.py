"""Add persisted work ratings.

Revision ID: b1e7a4c92d60
Revises: 41c6b8d2e950
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1e7a4c92d60"
down_revision: Union[str, Sequence[str], None] = "41c6b8d2e950"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calificacion",
        sa.Column("id_calificacion", sa.Integer(), nullable=False),
        sa.Column("id_postulacion", sa.Integer(), nullable=False),
        sa.Column("id_cliente", sa.Integer(), nullable=False),
        sa.Column("id_prestador", sa.Integer(), nullable=False),
        sa.Column("puntuacion", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("puntuacion BETWEEN 1 AND 5", name="ck_calificacion_puntuacion"),
        sa.ForeignKeyConstraint(
            ["id_cliente"], ["usuario.id_usuario"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["id_postulacion"], ["postulacion.id_postulacion"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["id_prestador"], ["prestador_servicio.id_prestador"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id_calificacion"),
        sa.UniqueConstraint("id_postulacion", name="uq_calificacion_postulacion"),
    )
    op.create_index(
        op.f("ix_calificacion_id_calificacion"),
        "calificacion",
        ["id_calificacion"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_calificacion_id_calificacion"), table_name="calificacion")
    op.drop_table("calificacion")