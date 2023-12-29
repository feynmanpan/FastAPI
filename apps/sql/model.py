from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
##############################################################

Base = declarative_base()


class IPS(Base):
    __tablename__ = "ips"
    #
    ip = Column(String, primary_key=True)
    port = Column(String, nullable=False)
    now = Column(String, nullable=False)
    goodcnt = Column(Integer, nullable=False)


#
class TEST(Base):
    __tablename__ = "test"
    #
    ipa = Column(String, primary_key=True)
    porta = Column(String, nullable=False)
