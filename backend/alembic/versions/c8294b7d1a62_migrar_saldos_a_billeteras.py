"""migrar saldos de prestadores a billeteras

Revision ID: c8294b7d1a62
Revises: d40f8a9e3bc1
Create Date: 2026-10-16 16:14:47.264000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8294b7d1a62"
down_revision: Union[str, Sequence[str], None] = "d40f8a9e3bc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO billetera_credito (prestador_id, saldo_actual, fecha_actualizacion)
            SELECT id_prestador, saldo_creditos, CURRENT_TIMESTAMP
            FROM prestador_servicio
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO transaccion_credito (
                billetera_id, monto, tipo, referencia_tipo, descripcion, fecha_registro
            )
            SELECT billetera.id, prestador.saldo_creditos, 'BONIFICACION',
                   'saldo_inicial', 'Saldo inicial migrado a billetera',
                   CURRENT_TIMESTAMP
            FROM prestador_servicio AS prestador
            JOIN billetera_credito AS billetera
              ON billetera.prestador_id = prestador.id_prestador
            WHERE prestador.saldo_creditos > 0
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE prestador_servicio AS prestador
            SET saldo_creditos = billetera.saldo_actual
            FROM billetera_credito AS billetera
            WHERE billetera.prestador_id = prestador.id_prestador
            """
        )
    )
