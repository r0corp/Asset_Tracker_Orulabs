"""sync missing model columns

Revision ID: f1d3cafb0fb3
Revises: e91d3df19b25
Create Date: 2026-09-15 14:43:07.177183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1d3cafb0fb3'
down_revision = 'e91d3df19b25'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('purchase_price', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.alter_column('model',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=100),
               existing_nullable=True)


def downgrade():
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.alter_column('model',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
        batch_op.drop_column('created_at')
        batch_op.drop_column('description')
        batch_op.drop_column('purchase_price')