import os
from typing import List

from starlette.requests import Request

from admin import enums
# from examples.constants import BASE_DIR
from config import top_dir
from admin.models import (
    Admin,
    LOTTO,
    IPS,
    INFO,
    # Category,
    Config,
    # Product
)
from fastapi_admin.app import app
from fastapi_admin.enums import Method
from fastapi_admin.file_upload import FileUpload
from fastapi_admin.resources import Action, Dropdown, Field, Link, Model, ToolbarAction
from fastapi_admin.widgets import displays, filters, inputs

upload = FileUpload(uploads_dir=os.path.join(top_dir, "static", "uploads"))


# @app.register
# class Dashboard(Link):
#     label = "Dashboard"
#     icon = "fas fa-home"
#     url = "/admin"


@app.register
class AdminResource(Model):
    label = "Admin"
    model = Admin
    icon = "fas fa-user"
    page_pre_title = "admin list"
    page_title = "admin model"
    filters = [
        filters.Search(
            name="username",
            label="Name",
            search_mode="contains",
            placeholder="Search for username",
        ),
        filters.Date(name="created_at", label="CreatedAt"),
    ]
    fields = [
        "id",
        "username",
        Field(
            name="password",
            label="Password",
            display=displays.InputOnly(),
            input_=inputs.Password(),
        ),
        Field(name="email", label="Email", input_=inputs.Email()),
        Field(
            name="avatar",
            label="Avatar",
            display=displays.Image(width="40"),
            input_=inputs.Image(null=True, upload=upload),
        ),
        "created_at",
    ]

    async def get_toolbar_actions(self, request: Request) -> List[ToolbarAction]:
        return []

    async def cell_attributes(self, request: Request, obj: dict, field: Field) -> dict:
        if field.name == "id":
            return {"class": "bg-danger text-white"}
        return await super().cell_attributes(request, obj, field)

    async def get_actions(self, request: Request) -> List[Action]:
        return []

    async def get_bulk_actions(self, request: Request) -> List[Action]:
        return []


@app.register
class Content(Dropdown):
    # 底下 resources 要加入 resource class
    class LOTTOResource(Model):
        label = "LOTTO"
        model = LOTTO
        filters = [
            filters.Filter(name="name", label="name="),
            filters.Filter(name="no", label="no="),
            filters.Filter(name="ymd", label="ymd="),
        ]
        fields = [
            "name",
            "no",
            "ymd",
            "area1",
            "area1asc",
            "area2",
            "salesamount",
            "totalbonus",
        ]

    class IPSResource(Model):
        label = "IPS"
        model = IPS
        filters = [
            filters.Filter(name="ip", label="ip="),
        ]
        fields = [
            "ip",
            "port",
            "now",
            "goodcnt"
        ]

    class INFOResource(Model):
        label = "INFO"
        model = INFO
        filters = [
            # filters.Search(
            #     name="bookid",
            #     label="bookid",
            #     search_mode="contains",
            #     placeholder="Search for bookid",
            # ),
            filters.Filter(name="idx", label="idx="),
            filters.Filter(name="bookid", label="bookid="),
            filters.Filter(name="isbn10", label="isbn10="),
            filters.Filter(name="isbn13", label="isbn13="),
        ]
        fields = [
            'idx',  # pk一定要秀，不然store會被整數處理
            'store',
            'bookid',
            'isbn10', 'isbn13',
            'title', 'price_list', 'stock', 'err',
            'create_dt'
        ]
    # class CategoryResource(Model):
    #     label = "Category"
    #     model = Category
    #     fields = ["id", "name", "slug", "created_at"]

    # class ProductResource(Model):
    #     label = "Product"
    #     model = Product
    #     filters = [
    #         filters.Enum(enum=enums.ProductType, name="type", label="ProductType"),
    #         filters.Datetime(name="created_at", label="CreatedAt"),
    #     ]
    #     fields = [
    #         "id",
    #         "name",
    #         "view_num",
    #         "sort",
    #         "is_reviewed",
    #         "type",
    #         Field(name="image", label="Image", display=displays.Image(width="40")),
    #         Field(name="body", label="Body", input_=inputs.Editor()),
    #         "created_at",
    #     ]

    label = "Content"
    icon = "fas fa-bars"
    resources = [
        LOTTOResource,
        IPSResource,
        INFOResource,
        # ProductResource,
        # CategoryResource,
    ]


@app.register
class ConfigResource(Model):
    label = "Config"
    model = Config
    icon = "fas fa-cogs"
    filters = [
        filters.Enum(enum=enums.Status, name="status", label="Status"),
        filters.Search(name="key", label="Key", search_mode="equal"),
    ]
    fields = [
        "id",
        "label",
        "key",
        "value",
        Field(
            name="status",
            label="Status",
            input_=inputs.RadioEnum(enums.Status, default=enums.Status.on),
        ),
    ]

    async def row_attributes(self, request: Request, obj: dict) -> dict:
        if obj.get("status") == enums.Status.on:
            return {"class": "bg-green text-white"}
        return await super().row_attributes(request, obj)

    async def get_actions(self, request: Request) -> List[Action]:
        actions = await super().get_actions(request)
        switch_status = Action(
            label="Switch Status",
            icon="ti ti-toggle-left",
            name="switch_status",
            method=Method.PUT,
        )
        actions.append(switch_status)
        return actions


@app.register
class GithubLink(Link):
    label = "Github"
    url = "https://github.com/fastapi-admin/fastapi-admin"
    icon = "fab fa-github"
    target = "_blank"


@app.register
class DocumentationLink(Link):
    label = "Documentation"
    url = "https://fastapi-admin.github.io"
    icon = "fas fa-file-code"
    target = "_blank"


@app.register
class ProLink(Link):
    label = "Pro Version"
    url = "https://fastapi-admin-pro.long2ice.cn/admin/login"
    icon = "far fa-heart"
    target = "_blank"


@app.register
class FastDoc(Link):
    label = "API文件"
    url = "/docs"
    icon = "far fa-heart"
    target = "_blank"


@app.register
class tts_pptx(Link):
    label = "投影片備忘錄轉語音"
    url = "/tts/pptx"
    icon = "far fa-heart"
    target = "_blank"


@app.register
class emotion(Link):
    label = "Google NLP 情緒指標"
    url = "/emotion"
    icon = "far fa-heart"
    target = "_blank"
