"""empty message

Revision ID: daecbb96491f
Revises: e4b7649dfbb3
Create Date: 2024-10-10 16:50:50.957160

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'daecbb96491f'
down_revision = 'e4b7649dfbb3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post_applicants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attributes', sa.PickleType(), nullable=True))
        batch_op.drop_column('content')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post_applicants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False))
        batch_op.drop_column('attributes')

    # ### end Alembic commands ###
