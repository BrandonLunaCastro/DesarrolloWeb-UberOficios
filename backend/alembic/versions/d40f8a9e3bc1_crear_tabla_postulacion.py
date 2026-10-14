"""Create job application table."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d40f8a9e3bc1"
down_revision: Union[str, Sequence[str], None] = (
    "a7f25cbd9014",
    "17ef4b706b59",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "postulacion",
        sa.Column("id_postulacion", sa.Integer(), nullable=False),
        sa.Column("id_aviso", sa.Integer(), nullable=False),
        sa.Column("id_prestador", sa.Integer(), nullable=False),
        sa.Column("presupuesto", sa.Numeric(12, 2), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column(
            "fecha_postulacion",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("estado", sa.String(length=30), server_default="PENDIENTE", nullable=False),
        sa.ForeignKeyConstraint(["id_aviso"], ["aviso.id_aviso"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["id_prestador"],
            ["prestador_servicio.id_prestador"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id_postulacion"),
        sa.UniqueConstraint(
            "id_aviso",
            "id_prestador",
            name="uq_postulacion_aviso_prestador",
        ),
    )
    op.create_index(
        op.f("ix_postulacion_id_postulacion"),
        "postulacion",
        ["id_postulacion"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_postulacion_id_postulacion"), table_name="postulacion")
    op.drop_table("postulacion")