from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, SmallInteger, Float
from tortoise.fields.data import FloatField
#
from apps.sql.config import Base


##############################################################
class LOTTO(Base):
    __tablename__ = "lotto"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    #
    name = Column(String(10), nullable=True)
    no = Column(String(9), nullable=True, index=True)
    ymd = Column(String(9), nullable=True)
    area1 = Column(String(17), nullable=True)
    area1asc = Column(String(17), nullable=True)
    area2 = Column(String(2), nullable=True)
    #
    create_dt = Column(String, nullable=True)
