# netstat -ltnp | grep 6001
# 顯示第一個監聽6001的process
# ps -aux | grep main
# 顯示一共連續三個process，都要kill
# uvicorn main:app --host 0.0.0.0 --port 6001 --reload --ssl-keyfile=/etc/letsencrypt/live/wtb.wtbwtb.tk/privkey.pem --ssl-certfile=/etc/letsencrypt/live/wtb.wtbwtb.tk/cert.pemcrypt/live/wtb.wtbwtb.tk/privkey.pem --ssl-certfile=/etc/letsencrypt/l
#################### import ################################
from typing import Optional, Callable
import asyncio
import os
# _____________________________________________________________________
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse, PlainTextResponse
from pydantic.networks import HttpUrl
from starlette.middleware.sessions import SessionMiddleware
from pydantic.tools import parse_obj_as
# _____________________________________________________________________
import config
from views import startBGT, test, totest
from middlewares import mw_list, check_isTH, check_isCORS, session_build
from utils import MSG, hash_str
# apps
from apps.pig.views import pig_d
#
from apps.ips.config import get_freeproxy_delta
from apps.ips.views import show_freeproxy, get_next_ip, check_proxy
#
import apps.book.classes as zimportall  # 載入所有subclass，使其註冊入BOOKBASE
from apps.book.views import (
    show_base,
    show_info,
    show_book,
)
#
import apps.sql.config as sqlcfg
from apps.sql.views import dbwtb_isconnected, redis_kv
#from apps.tts.views import tts_pptx, tts_pptx_handle
#from apps.NLP.views import emotion, emotion_handle
from apps.lottery.views import showsuper
#from apps.googledrive.views import uploadgd
#from apps.multipart.views import mp
from apps.numG.views import show_G
from apps.gameABB.views import (
    indexABB,
    wsself,
    wsgame,
)
from apps.line import send_line_notify
#################### admin ################################
#from admin import resources, routes
#from admin.providers import LoginProvider
#from admin.models import Admin
from config import (
    top_dir,
    DATABASE_URL,
    REDIS_URL,
    pathABB,
    secret,
)
#import aioredis
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from starlette.exceptions import HTTPException as StarletteHTTPException
#from tortoise.contrib.fastapi import register_tortoise
#from fastapi_admin.app import app as admin_app
'''
from fastapi_admin.exceptions import (
    forbidden_error_exception,
    not_found_error_exception,
    server_error_exception,
)
'''

#################### app ################################
app = FastAPI(
    openapi_url=f"/{secret}/openapi.json",
    docs_url=f"/{secret}/docs",
    redoc_url=None,
    #
    title="FastAPI",
    description="",
    version="1.0.0",
    openapi_tags=[
        {
            'name': '樂透分析',
            'description': '威力彩/大樂透/今彩539',
        },
        {
            'name': 'Google NLP',
            'description': '情緒指標',
            # "externalDocs": {
            #     "description": "來源",
            #     "url": "http://ppg.naif.org.tw/naif/MarketInformation/Poultry/TranStatistics.aspx",
            # },
        },
        {
            'name': 'Google Text-To-Speech',
            'description': '文字轉語音',
        },
        {
            'name': 'Google Drive',
            'description': '上傳雲端硬碟',
        },
        {
            'name': 'apps: ips',
            'description': 'proxy相關',
        },
        {
            'name': 'apps: book',
            'description': 'book相關',
        },
        {
            'name': 'apps: pig',
            'description': '規格豬日行情',
        },
        {
            'name': 'Websocket',
            'description': '實作對戰',
        },
        {
            'name': 'Test',
            'description': '測試',
        },
    ],
)
app.mount(f"/{config.static}", StaticFiles(directory=config.static), name=config.static)
#


def path_ws(url: str, func: Callable, **kwargs):
    return app.websocket(url, **kwargs)(func)


def path_get(url: str, func: Callable, **kwargs):
    return app.get(url, **kwargs)(func)


def path_post(url: str, func: Callable, **kwargs):
    return app.post(url, **kwargs)(func)


def path_MW(func: Callable):
    if func is check_isTH:
        return app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=func(),
        )
    elif func is check_isCORS:
        return app.add_middleware(
            CORSMiddleware,
            allow_origins=func(),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    elif func is session_build:
        secret_key = func()
        print(f'{secret_key=}')
        return app.add_middleware(SessionMiddleware, secret_key=secret_key)
    else:
        return app.middleware("http")(func)


#################### exception_handler ################################


#################### PG_DBWTB ################################


@app.on_event("startup")
async def startup():
    #await sqlcfg.dbwtb.connect()
    print(f">>>>>>>>>>>>>>> sqlcfg.dbwtb 連線 = {sqlcfg.dbwtb.is_connected} <<<<<<<<<<<<<<<")
    ###################################
    """
    redis = aioredis.from_url(
        REDIS_URL,
        decode_responses=True,
        encoding="utf8",
    )
    await admin_app.configure(
        logo_url="https://preview.tabler.io/static/logo-white.svg",
        template_folders=[os.path.join(top_dir, "admin", "templates")],
        favicon_url=parse_obj_as(HttpUrl, "https://raw.githubusercontent.com/fastapi-admin/fastapi-admin/dev/images/favicon.png"),
        providers=[
            LoginProvider(
                login_logo_url="https://preview.tabler.io/static/logo.svg",
                admin_model=Admin,
            )
        ],
        redis=redis,
    )
    """
    # await admin_app.init(
    #     admin_secret="test",
    #     permission=True,
    #     site=Site(
    #         name="FastAPI-Admin DEMO",
    #         login_footer="FASTAPI ADMIN - FastAPI Admin Dashboard",
    #         login_description="FastAPI Admin Dashboard",
    #         locale="en-US",
    #         locale_switcher=True,
    #         theme_switcher=True,
    #     ),
    # )


@app.on_event("shutdown")
async def shutdown():
    zimportall.BOOKBASE.top_proxy_tocsv()
    await zimportall.BOOKBASE.close_ss()
    await sqlcfg.dbwtb.connect()

#################### middlewares ################################
for mw in mw_list:
    path_MW(mw)
#


#################### url dispatch ################################
# lottery
path_get("/lotto/super", showsuper, tags=["樂透分析"], include_in_schema=True)
# Google
#path_get("/tts/pptx", tts_pptx, tags=["Google Text-To-Speech"])
#path_post("/tts/pptx_handle", tts_pptx_handle, tags=["Google Text-To-Speech"])
#path_get("/emotion", emotion, tags=["Google NLP"])
#path_post("/emotion_handle", emotion_handle, tags=["Google NLP"])
#path_get(f"/{secret}/uploadgd", uploadgd, tags=["Google Drive"])
# proxy
path_get("/proxy", show_freeproxy, tags=["apps: ips"])
path_get("/nextip", get_next_ip, tags=["apps: ips"])
path_get("/check_proxy", check_proxy, tags=["apps: ips"])
# book
path_get("/sb", show_base, tags=["apps: book"])
path_get("/show_info", show_info, tags=["apps: book"])
path_get("/info/{store}/{bookid}", show_book, tags=["apps: book"])
# pig
path_get("/pig_d", pig_d, tags=["apps: pig"])
# test
#path_get("/test/{p}/{q}", test, tags=["Test"])
path_get("/test/{p}", test, tags=["Test"])
path_get("/dbwtb", dbwtb_isconnected, tags=["Test"])
path_get("/redis", redis_kv, tags=["Test"])
path_get("/totest", totest, tags=["Test"], include_in_schema=True)
#path_get("/mp", mp, tags=["Test"])
path_get("/showG", show_G, tags=["Test"])
path_get("/line", send_line_notify, tags=["Test"])
#
path_get(pathABB, indexABB, tags=["Websocket"])
path_get("/", indexABB)
path_ws("/wsself", wsself)
path_ws("/wsgame", wsgame)
#
#################### schedule ################################
path_get("/startBGT", startBGT, include_in_schema=False)
if config.startBGT_atonce:
    asyncio.create_task(startBGT())
#################### admin ################################

'''
@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url=pathABB)
'''
#admin_app.add_exception_handler(HTTP_500_INTERNAL_SERVER_ERROR, server_error_exception)
#admin_app.add_exception_handler(HTTP_404_NOT_FOUND, not_found_error_exception)
#admin_app.add_exception_handler(HTTP_403_FORBIDDEN, forbidden_error_exception)
#app.mount(f"/admin", admin_app)
"""
register_tortoise(
    app,
    config={
        "connections": {"default": DATABASE_URL},
        "apps": {
            "models": {
                "models": ["admin.models"],
                "default_connection": "default",
            }
        },
    },
    generate_schemas=True,
)
"""

#################### MSG ################################
msgs = [
    f'頂層工作目錄:【{config.top_dir}】',
    f'執行模式:【{config.now_mode}】',
    f'''
    {config.middle_check_ipAuth=},
    {config.middle_check_isMT=},
    {config.middle_check_isTH=},
        {config.allowed_hosts=},
    {config.middle_check_isCORS=},
        {config.allowed_origins=},
    {config.middle_header_add=},
    {config.middle_session_build=},
    ''',
    f'在main啟動時執行排程startBGT: 【{config.startBGT_atonce}】',
    f'get_freeproxy 代理ip更新週期(秒): {get_freeproxy_delta}',
    f'BOOKBASE.top_proxy: {len(zimportall.BOOKBASE.top_proxy)} 個',
]

MSG.prt_msgs(msgs)
