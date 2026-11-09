"""Add client idempotency keys to chat messages.

Revision ID: 41c6b8d2e950
Revises: 2b7c9a1d4e60
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "41c6b8d2e950"
down_revision: Union[str, Sequence[str], None] = "2b7c9a1d4e60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mensaje",
        sa.Column("identificador_unico", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_mensaje_identificador_cliente",
        "mensaje",
        ["conversacion_id", "remitente_id", "identificador_unico"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_mensaje_identificador_cliente",
        "mensaje",
        type_="unique",
    )
    op.drop_column("mensaje", "identificador_unico")
