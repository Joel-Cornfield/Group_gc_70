"""Add explicit constraint names

Revision ID: 21497f205fe0
Revises: 2858162cb832
Create Date: 2025-04-29 15:47:10.371188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21497f205fe0'
down_revision = '2858162cb832'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('game_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_time', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
        batch_op.add_column(sa.Column('finish_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('total_score', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('locations_guessed', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('correct_guesses', sa.Integer(), nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('fk_game_history_user_id', 'user', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_column('time_finished')
        batch_op.drop_column('guess_location')
        batch_op.drop_column('result')
        batch_op.drop_column('guess_time')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('game_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('guess_time', sa.DATETIME(), nullable=False))
        batch_op.add_column(sa.Column('result', sa.VARCHAR(length=120), nullable=False))
        batch_op.add_column(sa.Column('guess_location', sa.VARCHAR(length=120), nullable=False))
        batch_op.add_column(sa.Column('time_finished', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint('fk_game_history_user_id', type_='foreignkey')
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])
        batch_op.drop_column('correct_guesses')
        batch_op.drop_column('locations_guessed')
        batch_op.drop_column('total_score')
        batch_op.drop_column('finish_time')
        batch_op.drop_column('start_time')

    # ### end Alembic commands ###
