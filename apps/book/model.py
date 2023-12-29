from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, SmallInteger, Float
#from tortoise.fields.data import FloatField
#
from apps.sql.config import Base


##############################################################
class INFO(Base):
    __tablename__ = "info"
    #
    idx = Column(Integer, primary_key=True, autoincrement=True)
    #
    store = Column(String(10), nullable=True)
    bookid = Column(String(20), nullable=True, index=True)
    isbn10 = Column(String(10), nullable=True)
    isbn13 = Column(String(13), nullable=True)
    title = Column(String, nullable=True)
    title2 = Column(String, nullable=True)
    author = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    pub_dt = Column(String, nullable=True)
    lang = Column(String, nullable=True)
    #
    price_list = Column(SmallInteger, nullable=True)
    price_sale = Column(Float, nullable=True)
    #
    stock = Column(String, nullable=True)
    spec = Column(String, nullable=True)
    intro = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    url_book = Column(String, nullable=True)
    url_vdo = Column(String, nullable=True)
    url_cover = Column(String, nullable=True)
    lock18 = Column(Boolean, nullable=True)
    err = Column(String, nullable=True)
    #
    create_dt = Column(String, nullable=True)
