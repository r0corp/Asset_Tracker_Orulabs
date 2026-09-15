"""add movement number

Revision ID: 70e58834de65
Revises: b45cec4015ff
Create Date: 2026-08-08 18:21:12.937918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70e58834de65'
down_revision = 'b45cec4015ff'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        'asset_movements',
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                'movement_no',
                sa.String(length=30),
                nullable=True
            )
        )

        batch_op.create_unique_constraint(
            'uq_asset_movements_movement_no',
            ['movement_no']
        )


def downgrade():
    with op.batch_alter_table(
        'asset_movements',
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            'uq_asset_movements_movement_no',
            type_='unique'
        )

        batch_op.drop_column(
            'movement_no'
        )
