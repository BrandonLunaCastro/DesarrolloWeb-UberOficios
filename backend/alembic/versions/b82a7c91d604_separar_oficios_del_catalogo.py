"""Agregar oficios separados al catálogo de categorías.

Revision ID: b82a7c91d604
Revises: a3c6d9e2f410
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b82a7c91d604"
down_revision: Union[str, Sequence[str], None] = "a3c6d9e2f410"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    for nombre in ("Plomería", "Gas", "Mecánica"):
        connection.execute(
            sa.text(
                """
                INSERT INTO categoria (nombre)
                SELECT :nombre
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM categoria
                    WHERE lower(trim(nombre)) = lower(trim(:nombre))
                )
                """
            ),
            {"nombre": nombre},
        )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            DELETE FROM categoria
            WHERE nombre IN ('Plomería', 'Gas', 'Mecánica')
              AND NOT EXISTS (
                  SELECT 1
                  FROM aviso
                  WHERE aviso.id_categoria = categoria.id_categoria
              )
            """
        )
    )
