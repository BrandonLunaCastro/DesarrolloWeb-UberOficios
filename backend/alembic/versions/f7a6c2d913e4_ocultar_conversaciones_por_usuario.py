"""Allow each participant to hide a conversation from their own list."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a6c2d913e4"
down_revision: Union[str, Sequence[str], None] = "c82f4a16d930"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversacion",
        sa.Column(
            "oculta_para_cliente",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "conversacion",
        sa.Column(
            "oculta_para_prestador",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("conversacion", "oculta_para_prestador")
    op.drop_column("conversacion", "oculta_para_cliente")
