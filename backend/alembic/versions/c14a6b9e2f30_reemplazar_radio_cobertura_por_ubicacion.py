"""Replace provider coverage radius with a service zone.

Revision ID: c14a6b9e2f30
Revises: 8c6f2d91a4b7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c14a6b9e2f30"
down_revision: Union[str, Sequence[str], None] = "8c6f2d91a4b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestador_servicio",
        sa.Column("zona", sa.String(length=150), nullable=True),
    )
    op.drop_column("prestador_servicio", "radio_cobertura_km")


def downgrade() -> None:
    op.add_column(
        "prestador_servicio",
        sa.Column("radio_cobertura_km", sa.Integer(), nullable=True),
    )
    op.drop_column("prestador_servicio", "zona")
