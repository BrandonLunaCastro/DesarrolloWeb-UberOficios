"""Track monthly provider credit bonuses."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f25cbd9014"
down_revision: Union[str, Sequence[str], None] = "9c4b6e2a1d70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prestador_servicio",
        sa.Column(
            "inicio_ciclo_creditos",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column(
            "meses_creditos_otorgados",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.execute(
        sa.text(
            "UPDATE prestador_servicio "
            "SET inicio_ciclo_creditos = CURRENT_TIMESTAMP "
            "WHERE inicio_ciclo_creditos IS NULL"
        )
    )
    op.alter_column(
        "prestador_servicio",
        "inicio_ciclo_creditos",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("prestador_servicio", "meses_creditos_otorgados")
    op.drop_column("prestador_servicio", "inicio_ciclo_creditos")
