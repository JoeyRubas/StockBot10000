"""Initial migration

Revision ID: 91877507502a
Revises: 
Create Date: 2025-03-18 08:42:01.819736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91877507502a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('portfolios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cash', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('positions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticker', sa.String(), nullable=False),
    sa.Column('shares', sa.Float(), nullable=False),
    sa.Column('share_price', sa.Float(), nullable=False),
    sa.Column('purchase_timestamp', sa.Float(), nullable=True),
    sa.Column('portfolio_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('positions')
    op.drop_table('portfolios')
    # ### end Alembic commands ###
