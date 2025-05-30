"""Added field to track friend request status

Revision ID: bf2151ea0914
Revises: 0210dda9a8e2
Create Date: 2025-05-08 13:22:05.885724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf2151ea0914'
down_revision = '0210dda9a8e2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('friend', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('friend', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###