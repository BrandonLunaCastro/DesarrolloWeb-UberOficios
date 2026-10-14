"""merge de ramas de migraciones

Revision ID: cad2f654bdf8
Revises: 9c4b6e2a1d70, c14a6b9e2f30
Create Date: 2026-10-14 12:27:04.842895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cad2f654bdf8'
down_revision: Union[str, Sequence[str], None] = ('9c4b6e2a1d70', 'c14a6b9e2f30')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
