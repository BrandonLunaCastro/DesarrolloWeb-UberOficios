"""Relacionar cada conversación con el presupuesto aceptado."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "be31f2a9c601"
down_revision: Union[str, Sequence[str], None] = "6ac774a5bb45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversacion",
        sa.Column("id_postulacion", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversacion_postulacion",
        "conversacion",
        "postulacion",
        ["id_postulacion"],
        ["id_postulacion"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_conversacion_id_postulacion",
        "conversacion",
        ["id_postulacion"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_conversacion_id_postulacion",
        "conversacion",
        type_="unique",
    )
    op.drop_constraint(
        "fk_conversacion_postulacion",
        "conversacion",
        type_="foreignkey",
    )
    op.drop_column("conversacion", "id_postulacion")
