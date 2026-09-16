"""add user security_stamp

Revision ID: 999651ebb026
Revises: b4fedc352d85
Create Date: 2026-09-17 00:00:00.000000

"""
import secrets

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '999651ebb026'
down_revision = 'b4fedc352d85'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('security_stamp', sa.String(length=64), nullable=True))

    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT id FROM users")).fetchall()

    for (user_id,) in users:
        conn.execute(
            sa.text("UPDATE users SET security_stamp = :stamp WHERE id = :id"),
            {"stamp": secrets.token_hex(32), "id": user_id},
        )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('security_stamp', existing_type=sa.String(length=64), nullable=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('security_stamp')
