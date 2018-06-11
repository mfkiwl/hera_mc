"""add weather table

Revision ID: 38aa03a7c923
Revises: c0985153bf41
Create Date: 2017-11-15 03:03:15.497948+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38aa03a7c923'
down_revision = 'c0985153bf41'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('weather_data',
    sa.Column('time', sa.BigInteger(), nullable=False),
    sa.Column('variable', sa.String(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('time', 'variable')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('weather_data')
    # ### end Alembic commands ###