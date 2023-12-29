from typing import Optional, Callable
from time import sleep
from datetime import datetime
import asyncio
import os
from os import path
from typing import Union, Optional
import json
#
from starlette.templating import _TemplateResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse, JSONResponse,Response
from fastapi import Request, BackgroundTasks, Path, Query, Depends
#
import config
from utils import static_makeornot
from tasks import tasks_list, check_task_exception
import apps.ips.config as ips_cfg
###############################################################################


startBGT_tasks: Optional[list] = None


async def startBGT():
    global startBGT_tasks
    if startBGT_tasks is None:
        startBGT_tasks = [asyncio.create_task(task(*args)) for task, args in tasks_list]
        asyncio.create_task(check_task_exception(startBGT_tasks))
        #
        print('>>>>>>>>>>>>>>> startBGT Running <<<<<<<<<<<<<<<')
        return '開始_幕後排程'
    else:
        NL = '\n\n'
        rep = f'幕後排程 running:{NL}{NL.join([str(t) for t in startBGT_tasks])}'
        return PlainTextResponse(rep)


# 沒有await就不要async，一般def會加開thread
# async def test(
#     res:Response,
#     request: Request,
#     p: str = "1",
#     q: int = 2,  # Path(..., title="QQQ"),
#     r: str = None,  # Query(..., title="RRR", ge=1),

# ):# -> _TemplateResponse:
#     if (plen := len(p)) > 2:
#         print(f'path len={plen}')
#     # sleep(10)
#     await asyncio.sleep(0)
#     print(f"p={p},q={q},r={r is None}")
#     print(f'locals()={locals()}')
#     # _______________________________________________
#     if request.query_params.get('q') is None:
#         print('qyery "q" 要有!')
#     #
# #     tmp1 = set(locals().keys())
# #     tmp2 = set(request.query_params.keys())
# #     tmpd = tmp2 - tmp1
# #     for k in tmpd:
# #         print(f'多的query參數: {k}')
# #     # _______________________________________________

# #     fn_static = f'test_{p}_{q}.html'
# #     fn_temp = "test.html"
# #     context = {
# #         'request': request,  # 一定要有
# #         'req_str': type(request),
# #         "p": p,
# #         "q": q,
# #     }
#     #
#     #return static_makeornot(fn_static, fn_temp, context)
#     #res.body = json.dumps({"A": 2}).encode('utf-8')
#     a=Response()
#     a.body=b"2sss"    
#     res.set_cookie(key="fakesession", value="fake-cookie-session-value")
#     return a


class CS:
    def __init__(self, req: Request):
        self.success = bool(req.cookies.get("token"))
        self.cookies_dict = req.cookies
        self.cookies_str = ';'.join(f'{k}={v}' for k, v in req.cookies.items())

# async def test(cs: CS = Depends(),p:int=1,/):
async def test(q,p:int=1):
#     if not cs.success:
#         return "沒有token"
#     return cs.cookies_str
    return HTMLResponse("<h1>2</h1>")

async def totest(request: Request):
    '''timeout測試'''
    # await asyncio.sleep(10)
    # print(request.scope)
    while 1:
        await asyncio.sleep(2)
        print("\n" * 3 + "123__timeout測試" * 30 + "\n" * 3)
        # for t in asyncio.all_tasks():
        #     if hasattr(t, 'rid'):
        #         print(t.rid, id(request.scope['app']), str(request.url))
