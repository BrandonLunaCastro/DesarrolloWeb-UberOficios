"""Agregar datos de perfil y solicitudes de trabajo.

Revision ID: 9c4b6e2a1d70
Revises: c14a6b9e2f30
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c4b6e2a1d70"
down_revision: Union[str, Sequence[str], None] = "c14a6b9e2f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cliente", sa.Column("zona", sa.String(), nullable=True))
    op.add_column("cliente", sa.Column("telefono", sa.String(), nullable=True))
    op.add_column("prestador_servicio", sa.Column("oficio", sa.String(), nullable=True))
    op.create_table(
        "aviso",
        sa.Column("id_aviso", sa.Integer(), nullable=False),
        sa.Column("id_cliente", sa.Integer(), nullable=False),
        sa.Column("oficio", sa.String(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("zona", sa.String(), nullable=False),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("estado", sa.String(), nullable=False, server_default="pendiente"),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["id_cliente"], ["cliente.id_cliente"]),
        sa.PrimaryKeyConstraint("id_aviso"),
    )
    op.create_index(op.f("ix_aviso_id_aviso"), "aviso", ["id_aviso"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_aviso_id_aviso"), table_name="aviso")
    op.drop_table("aviso")
    op.drop_column("prestador_servicio", "oficio")
    op.drop_column("cliente", "telefono")
    op.drop_column("cliente", "zona")