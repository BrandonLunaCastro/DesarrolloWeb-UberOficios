"""Create credit packages and purchases.

Revision ID: 2b7c9a1d4e60
Revises: be31f2a9c601
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2b7c9a1d4e60"
down_revision: Union[str, Sequence[str], None] = "be31f2a9c601"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "paquete_credito",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=60), nullable=False, unique=True),
        sa.Column("cantidad_creditos", sa.Integer(), nullable=False),
        sa.Column("precio_centavos", sa.Integer(), nullable=False),
        sa.Column("moneda", sa.String(length=3), server_default="ARS", nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("orden", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("cantidad_creditos > 0", name="ck_paquete_credito_cantidad"),
        sa.CheckConstraint("precio_centavos > 0", name="ck_paquete_credito_precio"),
    )
    op.create_index("ix_paquete_credito_id", "paquete_credito", ["id"])
    op.bulk_insert(
        sa.table(
            "paquete_credito",
            sa.column("nombre", sa.String()),
            sa.column("cantidad_creditos", sa.Integer()),
            sa.column("precio_centavos", sa.Integer()),
            sa.column("moneda", sa.String()),
            sa.column("activo", sa.Boolean()),
            sa.column("orden", sa.Integer()),
        ),
        [
            {
                "nombre": "Inicial",
                "cantidad_creditos": 5,
                "precio_centavos": 300000,
                "moneda": "ARS",
                "activo": True,
                "orden": 1,
            },
            {
                "nombre": "Popular",
                "cantidad_creditos": 15,
                "precio_centavos": 750000,
                "moneda": "ARS",
                "activo": True,
                "orden": 2,
            },
            {
                "nombre": "Profesional",
                "cantidad_creditos": 40,
                "precio_centavos": 1600000,
                "moneda": "ARS",
                "activo": True,
                "orden": 3,
            },
        ],
    )

    op.create_table(
        "compra_credito",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "prestador_id",
            sa.Integer(),
            sa.ForeignKey("prestador_servicio.id_prestador", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "paquete_id",
            sa.Integer(),
            sa.ForeignKey("paquete_credito.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cantidad_creditos", sa.Integer(), nullable=False),
        sa.Column("precio_centavos", sa.Integer(), nullable=False),
        sa.Column("moneda", sa.String(length=3), nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "PENDIENTE",
                "APROBADA",
                "RECHAZADA",
                "CANCELADA",
                name="estado_compra_credito_enum",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("referencia_pago", sa.String(length=100), nullable=True),
        sa.Column(
            "transaccion_id",
            sa.Integer(),
            sa.ForeignKey("transaccion_credito.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("preferencia_pago_id", sa.String(length=100), nullable=True),
        sa.Column("url_pago", sa.String(length=2048), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("fecha_acreditacion", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cantidad_creditos > 0", name="ck_compra_credito_cantidad"),
        sa.CheckConstraint("precio_centavos > 0", name="ck_compra_credito_precio"),
        sa.UniqueConstraint("referencia_pago", name="uq_compra_credito_referencia_pago"),
        sa.UniqueConstraint("transaccion_id", name="uq_compra_credito_transaccion"),
    )
    op.create_index("ix_compra_credito_id", "compra_credito", ["id"])
    op.create_index(
        "ix_compra_credito_prestador_fecha",
        "compra_credito",
        ["prestador_id", "fecha_creacion"],
    )


def downgrade() -> None:
    op.drop_index("ix_compra_credito_prestador_fecha", table_name="compra_credito")
    op.drop_index("ix_compra_credito_id", table_name="compra_credito")
    op.drop_table("compra_credito")
    op.drop_index("ix_paquete_credito_id", table_name="paquete_credito")
    op.drop_table("paquete_credito")
