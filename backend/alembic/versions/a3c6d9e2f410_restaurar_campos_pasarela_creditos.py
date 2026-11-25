"""Restore Mercado Pago fields on credit purchases."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3c6d9e2f410"
down_revision: Union[str, Sequence[str], None] = "71e4c8a9d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compra_credito",
        sa.Column("referencia_pago", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "compra_credito",
        sa.Column("preferencia_pago_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "compra_credito",
        sa.Column("url_pago", sa.String(length=2048), nullable=True),
    )
    op.create_unique_constraint(
        "uq_compra_credito_referencia_pago",
        "compra_credito",
        ["referencia_pago"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_compra_credito_referencia_pago",
        "compra_credito",
        type_="unique",
    )
    op.drop_column("compra_credito", "url_pago")
    op.drop_column("compra_credito", "preferencia_pago_id")
    op.drop_column("compra_credito", "referencia_pago")
