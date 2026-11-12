"""Add persisted user notifications.

Revision ID: c82f4a16d930
Revises: b1e7a4c92d60
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c82f4a16d930"
down_revision: Union[str, Sequence[str], None] = "b1e7a4c92d60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notificacion",
        sa.Column("id_notificacion", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "leida",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_notificacion"),
    )
    op.create_index(
        op.f("ix_notificacion_id_notificacion"),
        "notificacion",
        ["id_notificacion"],
        unique=False,
    )
    op.create_index(
        "ix_notificacion_usuario_fecha",
        "notificacion",
        ["id_usuario", "fecha_creacion"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notificacion_usuario_fecha", table_name="notificacion")
    op.drop_index(op.f("ix_notificacion_id_notificacion"), table_name="notificacion")
    op.drop_table("notificacion")