"""Align authentication tables with the normalized PostgreSQL schema.

Revision ID: 8c6f2d91a4b7
Revises: 5fa6e0cf26d5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c6f2d91a4b7"
down_revision: Union[str, Sequence[str], None] = "5fa6e0cf26d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rol",
        sa.Column("id_rol", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id_rol"),
        sa.UniqueConstraint("nombre"),
    )
    op.bulk_insert(
        sa.table(
            "rol",
            sa.column("id_rol", sa.Integer()),
            sa.column("nombre", sa.String()),
            sa.column("descripcion", sa.String()),
        ),
        [
            {
                "id_rol": 1,
                "nombre": "CLIENTE",
                "descripcion": "Usuario consumidor que busca contratar servicios",
            },
            {
                "id_rol": 2,
                "nombre": "PRESTADOR",
                "descripcion": "Profesional o trabajador de oficio que ofrece sus servicios",
            },
            {
                "id_rol": 3,
                "nombre": "ADMIN",
                "descripcion": "Administrador del sistema",
            },
        ],
    )
    op.execute("SELECT setval('rol_id_rol_seq', (SELECT MAX(id_rol) FROM rol))")

    op.add_column("usuario", sa.Column("id_rol", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE usuario
        SET id_rol = CASE
            WHEN EXISTS (
                SELECT 1 FROM prestador_servicio
                WHERE prestador_servicio.id_usuario = usuario.id_usuario
            ) THEN 2
            ELSE 1
        END
        """
    )
    op.alter_column(
        "usuario",
        "nombre_apellido",
        new_column_name="nombre",
        existing_type=sa.String(),
        type_=sa.String(length=100),
    )
    op.add_column(
        "usuario",
        sa.Column("apellido", sa.String(length=100), nullable=True),
    )
    op.execute(
        """
        UPDATE usuario
        SET apellido = CASE
                WHEN position(' ' IN btrim(nombre)) > 0
                THEN substring(btrim(nombre) FROM position(' ' IN btrim(nombre)) + 1)
                ELSE ''
            END,
            nombre = split_part(btrim(nombre), ' ', 1)
        """
    )
    op.alter_column("usuario", "apellido", nullable=False)
    op.alter_column("usuario", "id_rol", nullable=False)
    op.alter_column(
        "usuario",
        "correo",
        new_column_name="email",
        existing_type=sa.String(),
        type_=sa.String(length=150),
    )
    op.alter_column(
        "usuario",
        "contrasena",
        new_column_name="password_hash",
        existing_type=sa.String(),
        type_=sa.String(length=255),
    )
    op.add_column("usuario", sa.Column("telefono", sa.String(length=20)))
    op.add_column("usuario", sa.Column("foto_perfil", sa.String(length=255)))
    op.add_column(
        "usuario",
        sa.Column(
            "fecha_registro",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.drop_column("usuario", "estado")
    op.drop_index("ix_usuario_correo", table_name="usuario")
    op.drop_index("ix_usuario_id_usuario", table_name="usuario")
    op.create_index("ix_usuario_email", "usuario", ["email"], unique=True)
    op.create_foreign_key(
        "fk_usuario_rol",
        "usuario",
        "rol",
        ["id_rol"],
        ["id_rol"],
        ondelete="RESTRICT",
        onupdate="CASCADE",
    )

    op.drop_table("cliente")
    op.create_table(
        "cliente",
        sa.Column("id_cliente", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"]),
        sa.PrimaryKeyConstraint("id_cliente"),
        sa.UniqueConstraint("id_usuario"),
    )
    op.create_index(
        op.f("ix_cliente_id_cliente"),
        "cliente",
        ["id_cliente"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO cliente (id_usuario)
        SELECT usuario.id_usuario
        FROM usuario
        JOIN rol ON rol.id_rol = usuario.id_rol
        WHERE rol.nombre = 'CLIENTE'
        """
    )

    op.execute(
        """
        CREATE TEMPORARY TABLE prestador_servicio_migration_data AS
        SELECT id_usuario, creditos FROM prestador_servicio
        """
    )
    op.drop_table("prestador_servicio")
    op.create_table(
        "prestador_servicio",
        sa.Column("id_prestador", sa.Integer(), nullable=False),
        sa.Column("matricula", sa.String(length=50), nullable=True),
        sa.Column("biografia", sa.Text(), nullable=True),
        sa.Column(
            "radio_cobertura_km",
            sa.Integer(),
            server_default=sa.text("10"),
            nullable=True,
        ),
        sa.Column(
            "saldo_creditos",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id_prestador"],
            ["usuario.id_usuario"],
            name="fk_prestador_usuario",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id_prestador"),
    )
    op.execute(
        """
        INSERT INTO prestador_servicio (id_prestador, saldo_creditos)
        SELECT id_usuario, creditos FROM prestador_servicio_migration_data
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE TEMPORARY TABLE prestador_servicio_migration_data AS
        SELECT id_prestador, saldo_creditos FROM prestador_servicio
        """
    )
    op.drop_table("prestador_servicio")
    op.create_table(
        "prestador_servicio",
        sa.Column("id_prestador", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("provincia", sa.String(), nullable=True),
        sa.Column("departamento", sa.String(), nullable=True),
        sa.Column("prom_calificacion", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("creditos", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"]),
        sa.PrimaryKeyConstraint("id_prestador"),
        sa.UniqueConstraint("id_usuario"),
    )
    op.execute(
        """
        INSERT INTO prestador_servicio (id_usuario, creditos, activo)
        SELECT id_prestador, saldo_creditos, true
        FROM prestador_servicio_migration_data
        """
    )

    op.drop_index(op.f("ix_cliente_id_cliente"), table_name="cliente")
    op.drop_table("cliente")
    op.create_table(
        "cliente",
        sa.Column("id_cliente", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("localidad", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"]),
        sa.PrimaryKeyConstraint("id_cliente"),
        sa.UniqueConstraint("id_usuario"),
    )
    op.create_index(
        op.f("ix_cliente_id_cliente"),
        "cliente",
        ["id_cliente"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO cliente (id_usuario)
        SELECT usuario.id_usuario
        FROM usuario
        JOIN rol ON rol.id_rol = usuario.id_rol
        WHERE rol.nombre = 'CLIENTE'
        """
    )

    op.drop_constraint("fk_usuario_rol", "usuario", type_="foreignkey")
    op.drop_index("ix_usuario_email", table_name="usuario")
    op.alter_column(
        "usuario",
        "nombre",
        new_column_name="nombre_apellido",
        existing_type=sa.String(length=100),
        type_=sa.String(),
    )
    op.execute(
        "UPDATE usuario SET nombre_apellido = btrim(nombre_apellido || ' ' || apellido)"
    )
    op.drop_column("usuario", "apellido")
    op.alter_column(
        "usuario",
        "email",
        new_column_name="correo",
        existing_type=sa.String(length=150),
        type_=sa.String(),
    )
    op.alter_column(
        "usuario",
        "password_hash",
        new_column_name="contrasena",
        existing_type=sa.String(length=255),
        type_=sa.String(),
    )
    op.drop_column("usuario", "fecha_registro")
    op.drop_column("usuario", "foto_perfil")
    op.drop_column("usuario", "telefono")
    op.add_column(
        "usuario",
        sa.Column("estado", sa.String(), server_default="activo", nullable=False),
    )
    op.drop_column("usuario", "id_rol")
    op.create_index("ix_usuario_correo", "usuario", ["correo"], unique=True)
    op.create_index("ix_usuario_id_usuario", "usuario", ["id_usuario"], unique=False)
    op.drop_table("rol")
