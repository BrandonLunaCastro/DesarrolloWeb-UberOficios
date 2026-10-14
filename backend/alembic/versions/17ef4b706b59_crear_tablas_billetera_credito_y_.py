"""crear tablas billetera_credito y transaccion_credito

Revision ID: 17ef4b706b59
Revises: cad2f654bdf8
Create Date: 2026-10-14 12:38:43.250542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '17ef4b706b59'
down_revision: Union[str, Sequence[str], None] = 'cad2f654bdf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tabla Billetera de Crédito
    op.create_table('billetera_credito',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prestador_id', sa.Integer(), nullable=False),
        sa.Column('saldo_actual', sa.Integer(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['prestador_id'], ['prestador_servicio.id_prestador'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prestador_id')
    )
    op.create_index(op.f('ix_billetera_credito_id'), 'billetera_credito', ['id'], unique=False)

    # 2. Tabla Transacción de Crédito
    op.create_table('transaccion_credito',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('billetera_id', sa.Integer(), nullable=False),
        sa.Column('monto', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.Enum('RECARGA', 'CONSUMO_POSTULACION', 'DEVOLUCION', 'BONIFICACION', name='tipotransaccionenum'), nullable=False),
        sa.Column('referencia_id', sa.Integer(), nullable=True),
        sa.Column('referencia_tipo', sa.String(length=50), nullable=True),
        sa.Column('descripcion', sa.String(length=255), nullable=True),
        sa.Column('fecha_registro', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['billetera_id'], ['billetera_credito.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaccion_credito_id'), 'transaccion_credito', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('transaccion_credito')
    op.drop_table('billetera_credito')