"""table create

Revision ID: 88ff2c6b3408
Revises: 
Create Date: 2021-05-01 19:05:24.425288

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88ff2c6b3408'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('info',
    sa.Column('idx', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('store', sa.String(length=10), nullable=True),
    sa.Column('bookid', sa.String(length=20), nullable=True),
    sa.Column('isbn10', sa.String(length=10), nullable=True),
    sa.Column('isbn13', sa.String(length=13), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('title2', sa.String(), nullable=True),
    sa.Column('author', sa.String(), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('pub_dt', sa.String(), nullable=True),
    sa.Column('lang', sa.String(), nullable=True),
    sa.Column('price_list', sa.SmallInteger(), nullable=True),
    sa.Column('price_sale', sa.SmallInteger(), nullable=True),
    sa.Column('stock', sa.String(), nullable=True),
    sa.Column('spec', sa.String(), nullable=True),
    sa.Column('intro', sa.String(), nullable=True),
    sa.Column('comment', sa.String(), nullable=True),
    sa.Column('url_book', sa.String(), nullable=True),
    sa.Column('url_vdo', sa.String(), nullable=True),
    sa.Column('url_cover', sa.String(), nullable=True),
    sa.Column('lock18', sa.Boolean(), nullable=True),
    sa.Column('err', sa.String(), nullable=True),
    sa.Column('create_dt', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('idx')
    )
    op.create_index(op.f('ix_info_bookid'), 'info', ['bookid'], unique=False)
    op.create_table('ips',
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('port', sa.String(), nullable=False),
    sa.Column('now', sa.String(), nullable=False),
    sa.Column('goodcnt', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('ip')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ips')
    op.drop_index(op.f('ix_info_bookid'), table_name='info')
    op.drop_table('info')
    # ### end Alembic commands ###
