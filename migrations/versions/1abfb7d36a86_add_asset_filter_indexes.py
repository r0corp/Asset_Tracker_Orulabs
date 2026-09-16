"""add indexes for common asset/movement filter columns

Revision ID: 1abfb7d36a86
Revises: 999651ebb026
Create Date: 2026-09-17 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '1abfb7d36a86'
down_revision = '999651ebb026'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assets_category'), ['category'])
        batch_op.create_index(batch_op.f('ix_assets_location'), ['location'])
        batch_op.create_index(batch_op.f('ix_assets_department'), ['department'])
        batch_op.create_index(batch_op.f('ix_assets_vendor'), ['vendor'])
        batch_op.create_index(batch_op.f('ix_assets_status'), ['status'])

    with op.batch_alter_table('asset_movements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_asset_movements_asset_id'), ['asset_id'])
        batch_op.create_index(batch_op.f('ix_asset_movements_movement_date'), ['movement_date'])


def downgrade():
    with op.batch_alter_table('asset_movements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_asset_movements_movement_date'))
        batch_op.drop_index(batch_op.f('ix_asset_movements_asset_id'))

    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assets_status'))
        batch_op.drop_index(batch_op.f('ix_assets_vendor'))
        batch_op.drop_index(batch_op.f('ix_assets_department'))
        batch_op.drop_index(batch_op.f('ix_assets_location'))
        batch_op.drop_index(batch_op.f('ix_assets_category'))
