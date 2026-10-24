"""Add the provider trade field.

Revision ID: f16b8c4d2e71
Revises: e15a7c3b9d42
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f16b8c4d2e71"
down_revision: Union[str, Sequence[str], None] = "e15a7c3b9d42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("prestador_servicio")
    }
    if "oficio" not in columns:
        op.add_column(
            "prestador_servicio",
            sa.Column("oficio", sa.String(length=100), nullable=True),
        )


def downgrade() -> None:
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("prestador_servicio")
    }
    if "oficio" in columns:
        op.drop_column("prestador_servicio", "oficio")
