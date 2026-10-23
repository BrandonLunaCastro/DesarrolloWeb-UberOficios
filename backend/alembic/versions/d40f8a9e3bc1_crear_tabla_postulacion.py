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
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("postulacion"):
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
    else:
        _upgrade_existing_postulacion(inspector)

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("postulacion")
    }
    if "ix_postulacion_id_postulacion" not in existing_indexes:
        op.create_index(
            op.f("ix_postulacion_id_postulacion"),
            "postulacion",
            ["id_postulacion"],
            unique=False,
        )


def _upgrade_existing_postulacion(inspector) -> None:
    column_info = {
        column["name"]: column
        for column in inspector.get_columns("postulacion")
    }
    columns = set(column_info)

    if "presupuesto" not in columns and "precio_ofertado" in columns:
        op.alter_column(
            "postulacion",
            "precio_ofertado",
            new_column_name="presupuesto",
            existing_type=column_info["precio_ofertado"]["type"],
        )
    elif "presupuesto" not in columns:
        raise RuntimeError(
            "La tabla postulacion existente no tiene precio_ofertado ni presupuesto"
        )

    if "comentario" not in columns and "mensaje_propuesta" in columns:
        op.alter_column(
            "postulacion",
            "mensaje_propuesta",
            new_column_name="comentario",
            existing_type=column_info["mensaje_propuesta"]["type"],
        )

    if "id_postulacion" not in columns:
        op.add_column(
            "postulacion",
            sa.Column("id_postulacion", sa.Integer(), nullable=True),
        )

    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS postulacion_id_postulacion_seq"))
    op.execute(
        sa.text(
            "UPDATE postulacion "
            "SET id_postulacion = nextval('postulacion_id_postulacion_seq') "
            "WHERE id_postulacion IS NULL"
        )
    )
    op.execute(
        sa.text(
            """
            SELECT setval(
                'postulacion_id_postulacion_seq',
                COALESCE(MAX(id_postulacion), 1),
                MAX(id_postulacion) IS NOT NULL
            )
            FROM postulacion
            """
        )
    )
    op.alter_column(
        "postulacion",
        "id_postulacion",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text("nextval('postulacion_id_postulacion_seq')"),
    )
    primary_key = inspector.get_pk_constraint("postulacion")
    if primary_key["constrained_columns"] != ["id_postulacion"]:
        if primary_key["name"]:
            op.drop_constraint(
                primary_key["name"],
                "postulacion",
                type_="primary",
            )
        op.create_primary_key(
            "postulacion_pkey",
            "postulacion",
            ["id_postulacion"],
        )
    unique_constraints = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("postulacion")
    }
    if ("id_aviso", "id_prestador") not in unique_constraints:
        op.create_unique_constraint(
            "uq_postulacion_aviso_prestador",
            "postulacion",
            ["id_aviso", "id_prestador"],
        )
    op.execute(
        sa.text(
            "ALTER SEQUENCE postulacion_id_postulacion_seq "
            "OWNED BY postulacion.id_postulacion"
        )
    )

    if "estado" not in columns:
        op.add_column(
            "postulacion",
            sa.Column(
                "estado",
                sa.String(length=30),
                nullable=False,
                server_default="PENDIENTE",
            ),
        )

    fecha = column_info["fecha_postulacion"]
    if isinstance(fecha["type"], sa.DateTime) and not fecha["type"].timezone:
        op.alter_column(
            "postulacion",
            "fecha_postulacion",
            existing_type=fecha["type"],
            type_=sa.DateTime(timezone=True),
            postgresql_using="fecha_postulacion AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_postulacion_id_postulacion"), table_name="postulacion")
    op.drop_table("postulacion")