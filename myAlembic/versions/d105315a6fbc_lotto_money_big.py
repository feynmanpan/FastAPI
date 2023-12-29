"""lotto money big

Revision ID: d105315a6fbc
Revises: 77def6230975
Create Date: 2021-11-29 12:37:37.688706

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd105315a6fbc'
down_revision = '77def6230975'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('lotto', 'salesamount',
                    type_=sa.BigInteger(),
                    existing_type=sa.INTEGER(),
                    existing_comment=None,
                    existing_nullable=True,
                    )
    #
    op.alter_column('lotto', 'totalbonus',
                    type_=sa.BigInteger(),
                    existing_type=sa.INTEGER(),
                    existing_comment=None,
                    existing_nullable=True,
                    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('lotto', 'salesamount',
                    type_=sa.INTEGER(),
                    existing_type=sa.BigInteger(),
                    existing_comment=None,
                    existing_nullable=True,
                    )
    #
    op.alter_column('lotto', 'totalbonus',
                    type_=sa.INTEGER(),
                    existing_type=sa.BigInteger(),
                    existing_comment=None,
                    existing_nullable=True,
                    )