"""lotto

Revision ID: 20bcfc3e706a
Revises: f0950885120f
Create Date: 2021-11-24 11:36:05.246655

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20bcfc3e706a'
down_revision = 'f0950885120f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lotto',
    sa.Column('idx', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=10), nullable=True),
    sa.Column('no', sa.String(length=9), nullable=True),
    sa.Column('ymd', sa.String(length=9), nullable=True),
    sa.Column('area1', sa.String(length=17), nullable=True),
    sa.Column('area1asc', sa.String(length=17), nullable=True),
    sa.Column('area2', sa.String(length=2), nullable=True),
    sa.Column('create_dt', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('idx')
    )
    op.create_index(op.f('ix_lotto_no'), 'lotto', ['no'], unique=False)
    op.drop_table('admin')
    op.drop_table('config')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('config',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('label', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('key', sa.VARCHAR(length=20), autoincrement=False, nullable=False, comment='Unique key for config'),
    sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('status', sa.SMALLINT(), server_default=sa.text('1'), autoincrement=False, nullable=False, comment='on: 1\\noff: 0'),
    sa.PrimaryKeyConstraint('id', name='config_pkey'),
    sa.UniqueConstraint('key', name='config_key_key')
    )
    op.create_table('admin',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('password', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('last_login', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False, comment='Last Login'),
    sa.Column('email', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('avatar', sa.VARCHAR(length=200), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False),
    sa.Column('intro', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='admin_pkey'),
    sa.UniqueConstraint('username', name='admin_username_key')
    )
    op.drop_index(op.f('ix_lotto_no'), table_name='lotto')
    op.drop_table('lotto')
    # ### end Alembic commands ###
