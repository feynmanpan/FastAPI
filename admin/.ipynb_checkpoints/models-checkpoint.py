import datetime

from tortoise import Model, fields

from admin.enums import ProductType, Status
from fastapi_admin.models import AbstractAdmin


class Admin(AbstractAdmin):
    last_login = fields.DatetimeField(description="Last Login", default=datetime.datetime.now)
    email = fields.CharField(max_length=200, default="")
    avatar = fields.CharField(max_length=200, default="")
    intro = fields.TextField(default="")
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pk}#{self.username}"

class LOTTO(Model):
    idx = fields.IntField(pk=True, null=False)
    #
    name = fields.CharField(max_length=10, null=True)
    no = fields.CharField(max_length=9, null=True)
    ymd = fields.CharField(max_length=9, null=True)
    area1 = fields.CharField(max_length=17, null=True)
    area1asc = fields.CharField(max_length=17, null=True)
    area2 = fields.CharField(max_length=2, null=True)
    #
    create_dt = fields.TextField(null=True)  
    

class IPS(Model):
    ip = fields.TextField(pk=True, null=False)
    port = fields.TextField(null=False)
    now = fields.TextField(null=False)
    goodcnt = fields.SmallIntField(null=False)
    # ip = Column(String, primary_key=True, nullable=False)  # unique=True,
    # port = Column(String, nullable=False)
    # now = Column(String, nullable=False)
    # goodcnt = Column(Integer, nullable=False)


class INFO(Model):
    #
    idx = fields.IntField(pk=True, null=False)  # Column(Integer, primary_key=True, autoincrement=True)
    #
    store = fields.CharField(max_length=10, null=True)  # Column(String(10), nullable=True)
    bookid = fields.CharField(max_length=20, null=True)  # Column(String(20), nullable=True, index=True)
    isbn10 = fields.CharField(max_length=10, null=True)  # Column(String(10), nullable=True)
    isbn13 = fields.CharField(max_length=13, null=True)  # Column(String(13), nullable=True)
    title = fields.TextField(null=True)  # Column(String, nullable=True)
    title2 = fields.TextField(null=True)  # Column(String, nullable=True)
    author = fields.TextField(null=True)  # Column(String, nullable=True)
    publisher = fields.TextField(null=True)  # Column(String, nullable=True)
    pub_dt = fields.TextField(null=True)  # Column(String, nullable=True)
    lang = fields.TextField(null=True)  # Column(String, nullable=True)
    #
    price_list = fields.SmallIntField(null=True)  # Column(SmallInteger, nullable=True)
    price_sale = fields.FloatField(null=True)  # Column(SmallInteger, nullable=True)
    #
    stock = fields.TextField(null=True)  # Column(String, nullable=True)
    spec = fields.TextField(null=True)  # Column(String, nullable=True)
    intro = fields.TextField(null=True)  # Column(String, nullable=True)
    comment = fields.TextField(null=True)  # Column(String, nullable=True)
    url_book = fields.TextField(null=True)  # Column(String, nullable=True)
    url_vdo = fields.TextField(null=True)  # Column(String, nullable=True)
    url_cover = fields.TextField(null=True)  # Column(String, nullable=True)
    lock18 = fields.BooleanField(null=True)  # Column(Boolean, nullable=True)
    err = fields.TextField(null=True)  # Column(String, nullable=True)
    #
    create_dt = fields.TextField(null=True)  # Column(String, nullable=True)


# class Category(Model):
#     slug = fields.CharField(max_length=200)
#     name = fields.CharField(max_length=200)
#     created_at = fields.DatetimeField(auto_now_add=True)


# class Product(Model):
#     categories = fields.ManyToManyField("models.Category")
#     name = fields.CharField(max_length=50)
#     view_num = fields.IntField(description="View Num")
#     sort = fields.IntField()
#     is_reviewed = fields.BooleanField(description="Is Reviewed")
#     type = fields.IntEnumField(ProductType, description="Product Type")
#     image = fields.CharField(max_length=200)
#     body = fields.TextField()
#     created_at = fields.DatetimeField(auto_now_add=True)


class Config(Model):
    label = fields.CharField(max_length=200)
    key = fields.CharField(max_length=20, unique=True, description="Unique key for config")
    value = fields.JSONField()
    status: Status = fields.IntEnumField(Status, default=Status.on)
