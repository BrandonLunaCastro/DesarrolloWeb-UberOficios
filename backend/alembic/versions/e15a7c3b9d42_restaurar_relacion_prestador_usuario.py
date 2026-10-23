"""Restore the provider-to-user relationship column.

Revision ID: e15a7c3b9d42
Revises: d40f8a9e3bc1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e15a7c3b9d42"
down_revision: Union[str, Sequence[str], None] = "d40f8a9e3bc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestador_servicio",
        sa.Column("id_usuario", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE prestador_servicio "
            "SET id_usuario = id_prestador"
        )
    )
    op.alter_column(
        "prestador_servicio",
        "id_usuario",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_constraint(
        "fk_prestador_usuario",
        "prestador_servicio",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_prestador_servicio_usuario",
        "prestador_servicio",
        "usuario",
        ["id_usuario"],
        ["id_usuario"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.create_unique_constraint(
        "uq_prestador_servicio_id_usuario",
        "prestador_servicio",
        ["id_usuario"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_prestador_servicio_id_usuario",
        "prestador_servicio",
        type_="unique",
    )
    op.drop_constraint(
        "fk_prestador_servicio_usuario",
        "prestador_servicio",
        type_="foreignkey",
    )
    op.drop_column("prestador_servicio", "id_usuario")
    op.create_foreign_key(
        "fk_prestador_usuario",
        "prestador_servicio",
        "usuario",
        ["id_prestador"],
        ["id_usuario"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
