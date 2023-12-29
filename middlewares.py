import re
import sys
import time
from datetime import datetime
import inspect
import functools
from typing import Optional, Callable
import asyncio
#
from fastapi import Request, HTTPException, status
from fastapi.responses import HTMLResponse, ORJSONResponse, JSONResponse, Response, RedirectResponse
#
from utils import hash_str
import config
from config import (
    MODES,
    now_mode,
    maintenance_allow_patterns,
    maintenance_html,
    ok_ips,
    ban_ips,
    allowed_origins,
    allowed_hosts,
    allowed_all,
    middle_check_ipAuth,
    middle_check_isCORS,
    middle_check_isMT,
    middle_check_isTH,
    middle_header_add,
    middle_session_build,
    middle_global_timeout,
    global_TO,
    pathABB,
    static,
)
from utils import print_func_name
########################################################


async def global_timeout(request: Request, call_next):
    '''middleware對每個request處理做限時'''
    # 要修改fastapi Lib\site-packages\starlette\middleware\base.py
    # vi /home/pan/anaconda3/envs/fast_env/lib/python3.9/site-packages/starlette/middleware/base.py
    # line 43 task.rid = id(request.scope), id(request.receive), str(request.url)
    # 每個task唯一對應 scope+receive
    rid = id(request.scope), id(request.receive), str(request.url)
    task = asyncio.create_task(call_next(request))
    #
    done, pending = await asyncio.wait({task}, timeout=global_TO)
    #
    if not done:
        #
        for t in asyncio.all_tasks():
            if t._coro.__name__ == 'coro' and hasattr(t, 'rid'):
                if t.rid == rid:
                    t.cancel()
        task.cancel()
        #
        return HTMLResponse(content="請求逾時!", status_code=408)
    else:
        return task.result()
        # return done.pop().result()


async def check_ipAuth(request: Request, call_next):
    '''限制允許的ip'''
    print_func_name()
    url = request.url._url
    path = request.url.path
    ip = request.client.host
    print(f"【Request】 {url=}, {path=}, {ip=}\n\n")
    #
    if 1:#ip in ok_ips:
        return await call_next(request)
    elif ip in ban_ips:
        msg = "請向網站管理員申請IP的訪問權"
        return ORJSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'msg': msg})
    else:
        if path != pathABB and static not in path:
            return RedirectResponse(url=pathABB)
        #
        return await call_next(request)


async def check_isMT(request: Request, call_next):
    '''確認執行模式是否維護'''
    print_func_name()
    print(f"{request.url.path=}")
    print(f"{request.url=}")
    if isMT := (now_mode == MODES.maintenance):
        for pattern in maintenance_allow_patterns:
            if re.match(pattern, request.url.path):   # DNS以後到?以前，維護模式下仍可訪問的path
                isMT = False
                break
    #
    if isMT:
        return config.jinja_templates.TemplateResponse(maintenance_html, {'request': request})
    else:
        return await call_next(request)


def check_isTH() -> list:
    '''
    避免 HTTP Host header attack
    return allowed_hosts or allowed_all
    '''
    return allowed_hosts or allowed_all


def check_isCORS() -> list:
    '''
    同源政策 CORS
    return allowed_origins or allowed_all
    '''
    return allowed_origins or allowed_all


async def header_add(request: Request, call_next):
    '''任意請求至回應的總處理時間'''
    print_func_name()
    #
    start_time = time.time()
    res = await call_next(request)
    process_time = time.time() - start_time
    #
    # content_type = res.headers['content-type']
    res.headers["X-Process-Time"] = str(process_time)
    res.headers['X-Content-Type-Options'] = 'nosniff'
    #
    return res


def session_build() -> str:
    '''
    產生 SessionMiddleware 需要的 secret_key
    '''
    secret_key = hash_str(raw=str(datetime.now()))
    return secret_key


def csrf_token_add(view_func: Callable) -> Callable:
    '''裝飾器: 在session及cookie中添加csrf_token
    根據 middle_session_build，回傳 view_func/wrapper
    '''
    @functools.wraps(view_func)
    async def wrapper(**kwargs):
        # server 以session紀錄token
        csrf_token = hash_str(raw=str(datetime.now()))
        kwargs['request'].session['csrf_token'] = csrf_token
        # view 處理回應
        rep = await view_func(**kwargs)
        # client 以cookie紀錄token
        rep.set_cookie(key="csrf_token", value=csrf_token)
        #
        return rep
    #
    return [view_func, wrapper][middle_session_build]


def csrf_token_check(view_func: Callable) -> Callable:
    '''裝飾器: 比對client回傳的header token與session的token
    根據 middle_session_build，回傳 view_func/wrapper
    '''
    @functools.wraps(view_func)
    async def wrapper(**kwargs):
        request = kwargs['request']
        #
        csrftoken_cookie = request.headers.get('csrf_token')
        csrftoken_ss = request.session.get('csrf_token')
        #
        cond1 = not csrftoken_cookie or not csrftoken_ss
        cond2 = csrftoken_cookie != csrftoken_ss
        cond = cond1 or cond2
        #
        msg = f"【CSRF_TOKEN】檢查 {['OK','NG'][cond]}: {['可','不可'][cond]}執行 {view_func.__name__}"
        print(msg)
        #
        if cond:
            raise HTTPException(status_code=404, detail="CSRF_TOKEN not found")
        else:
            return await view_func(**kwargs)
    #
    return [view_func, wrapper][middle_session_build]


# async def mwtest(request: Request, call_next):
#     print('中介測試')
#     client_host = request.client.host
#     html = f'''
#         <h1 style="color:blue">中介測試:{client_host}</h1>
#     '''
#     return HTMLResponse(html)


#################### app.middleware("http") ################################
# return 都要是response class，不能直接基本類型
# 由後先呼叫
mw_list = [
    # mwtest,
] +\
    [check_ipAuth] * middle_check_ipAuth +\
    [check_isMT] * middle_check_isMT +\
    [check_isTH] * middle_check_isTH +\
    [check_isCORS] * middle_check_isCORS +\
    [header_add] * middle_header_add +\
    [session_build] * middle_session_build +\
    [global_timeout] * middle_global_timeout  # 要放最後面
