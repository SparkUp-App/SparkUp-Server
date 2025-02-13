"""empty message

Revision ID: 26f388f6c287
Revises: 9952213747ef
Create Date: 2024-10-11 14:43:25.752067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26f388f6c287'
down_revision = '9952213747ef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_room_users', schema=None) as batch_op:
        batch_op.create_unique_constraint('_chat_room_user_uc', ['post_id', 'user_id'])
        batch_op.drop_constraint('chat_room_users_post_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'chat_rooms', ['post_id'], ['post_id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_room_users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('chat_room_users_post_id_fkey', 'posts', ['post_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_constraint('_chat_room_user_uc', type_='unique')

    # ### end Alembic commands ###
