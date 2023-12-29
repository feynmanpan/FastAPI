import sqlalchemy as sa
from sqlalchemy import (
    Table as TB,
    Boolean, Column, ForeignKey, Integer, String, SmallInteger
)
#
from apps.sql.config import Base, metadata


##############################################################
# 在env.py匯入此class
class IPS(Base):
    __tablename__ = "ips"
    #
    # idx = Column(Integer, primary_key=True, autoincrement=True)
    #
    ip = Column(String, primary_key=True, nullable=False)  # unique=True,
    port = Column(String, nullable=False)
    now = Column(String, nullable=False)
    goodcnt = Column(Boolean, nullable=False, comment='good count')


# 從Alembic的upgrade複製過來修改，但sa的ORM可以直接用上面的IPS
# tb_ips = TB('ips',
#             metadata,  # 加這個
#             sa.Column('idx', sa.Integer(), autoincrement=True, nullable=False),
#             sa.Column('ip', sa.String(), nullable=False),
#             sa.Column('port', sa.String(), nullable=False),
#             sa.Column('now', sa.String(), nullable=False),
#             sa.Column('goodcnt', sa.Integer(), nullable=False),
#             sa.PrimaryKeyConstraint('idx'),
#             sa.UniqueConstraint('ip')
#             )
