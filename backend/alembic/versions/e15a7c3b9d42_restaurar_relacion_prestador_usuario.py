"""Restore the provider-to-user relationship column.

Revision ID: e15a7c3b9d42
Revises: c8294b7d1a62
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e15a7c3b9d42"
down_revision: Union[str, Sequence[str], None] = "c8294b7d1a62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    prestador_columns = {
        column["name"]: column
        for column in inspector.get_columns("prestador_servicio")
    }
    op.add_column(
        "prestador_servicio",
        sa.Column("telefono", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column("provincia", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column("departamento", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column("prom_calificacion", sa.Numeric(precision=3, scale=2), nullable=True),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column(
            "creditos",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("10"),
        ),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "prestador_servicio",
        sa.Column("id_usuario", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE prestador_servicio "
            "SET id_usuario = id_prestador"
        )
    )
    op.alter_column(
        "prestador_servicio",
        "id_usuario",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_constraint(
        "fk_prestador_usuario",
        "prestador_servicio",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_prestador_servicio_usuario",
        "prestador_servicio",
        "usuario",
        ["id_usuario"],
        ["id_usuario"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.create_unique_constraint(
        "uq_prestador_servicio_id_usuario",
        "prestador_servicio",
        ["id_usuario"],
    )

    if prestador_columns["id_prestador"]["default"] is None:
        op.execute(
            sa.text(
                "CREATE SEQUENCE IF NOT EXISTS "
                "prestador_servicio_id_prestador_seq"
            )
        )
        op.execute(
            sa.text(
                """
                SELECT setval(
                    'prestador_servicio_id_prestador_seq',
                    COALESCE(MAX(id_prestador), 1),
                    MAX(id_prestador) IS NOT NULL
                )
                FROM prestador_servicio
                """
            )
        )
        op.alter_column(
            "prestador_servicio",
            "id_prestador",
            existing_type=sa.Integer(),
            server_default=sa.text(
                "nextval('prestador_servicio_id_prestador_seq')"
            ),
        )
        op.execute(
            sa.text(
                "ALTER SEQUENCE prestador_servicio_id_prestador_seq "
                "OWNED BY prestador_servicio.id_prestador"
            )
        )


def downgrade() -> None:
    op.drop_constraint(
        "uq_prestador_servicio_id_usuario",
        "prestador_servicio",
        type_="unique",
    )
    op.drop_constraint(
        "fk_prestador_servicio_usuario",
        "prestador_servicio",
        type_="foreignkey",
    )
    op.drop_column("prestador_servicio", "id_usuario")
    op.create_foreign_key(
        "fk_prestador_usuario",
        "prestador_servicio",
        "usuario",
        ["id_prestador"],
        ["id_usuario"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
