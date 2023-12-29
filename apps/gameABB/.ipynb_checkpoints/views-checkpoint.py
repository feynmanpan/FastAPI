from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, ORJSONResponse, Response, PlainTextResponse
from typing import Optional, Union
import json
from pyquery import PyQuery as pq
import asyncio
from datetime import datetime, timezone
import time, pytz
from random import sample
#
from .config import jinja_templates
from apps.gameABB.ABB import GAME, PLAYER, MAN
from apps.gameABB.lockbywait import WAITER
import apps.gameABB.config as cfg
########################################################
import boto3
import pandas as pd
from io import StringIO
import re
########################################################

def get_now_tw():
    tw = pytz.timezone('Asia/Taipei')
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    now_tw = tw.normalize(now_utc.astimezone(tw))
    #
    return now_tw

def savetos3(ans="", histry="", s3=False):
    now = get_now_tw().strftime("%Y%m%d_%H%M%S")
    fn=f'dev/abb_log/{ans}_{now}.csv'
    #
    arr = re.findall('[0-9]{4}.[0-9]A[0-9]B', histry)
    df = pd.DataFrame(arr)[0].str.split('➜', expand=True).iloc[::-1]
    df = df.rename(columns={0: "guess", 1: "compare"})
    df = df.reset_index(drop=True)
    df['ans']=ans
    #
    if not s3:
        fn=f'./apps/gameABB/ai_histry/{ans}_{now}.csv'
        df.to_csv(fn, index=False)
        return
    #
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    body = csv_buffer.getvalue()
    #
    s3 = boto3.resource("s3")
    bkn = "bk1234"
    bk1234 = s3.Bucket(bkn)    
    # 
    bk1234.put_object(Key=fn, Body=body)



def resByI(I: MAN, ajax: int = 0, domstr: int = 0) -> Union[Response, str]:
    '''
        利用模板處理回應
        ajax=0: 第一次get的頁面內容，之後ws都不需要，減少處理量
        domstr=0: ws只需要html字串
    '''
    context = {
        'request': I.req,
        'ajax': ajax,
        'I': I,
        'info': json.dumps(I.info, indent=2, ensure_ascii=False),
    }
    res = jinja_templates.TemplateResponse('show.html', context)
    #
    if domstr == 0:
        if I.isPlayer:
            res.set_cookie(key="pid", value=f"{I.pid}")
            res.set_cookie(key="pname", value=f"{I.pname}")
            res.set_cookie(key="ans", value=f"{I.ans}")
            res.set_cookie(key="gid", value=f"{I.gid}")
        else:
            res.delete_cookie(key="pid")
            res.delete_cookie(key="pname")
            res.delete_cookie(key="ans")
            res.delete_cookie(key="gid")
    else:
        res = res.body.decode('utf8')  # 只要domstr
    #
    return res


async def indexABB(request: Request):
    '''第一次get'''
    pid = request.cookies.get('pid', '')
    pname = request.cookies.get('pname', '')
    ans = request.cookies.get('ans', '')
    gid = request.cookies.get('gid', '')
    #
    I = await PLAYER.creat(pid=pid, pname=pname, ans=ans, gid=gid, req=request)
    #
    return resByI(I, 0, 0)


async def wsself(websocket: WebSocket):
    '''p1p2認證'''
    await websocket.accept()
    #
    try:
        while 1:
            init = json.loads(await websocket.receive_text())
            info = {'status': init['status']}
            #
            if info['status'] == cfg.const.newjoin:
                I = await PLAYER.creat(**init)
                info |= I.info
                dom = pq(resByI(I, 1, 1))
                info[cfg.const.domstr_main] = dom.find('#' + cfg.const.main).html()
                info[cfg.const.domstr_infoarea] = dom.find('#' + cfg.const.infoarea).html()
                #
            elif info['status'] == cfg.const.checkans:
                info |= init
                I: PLAYER = GAME.players.get(info['pid'])
                he: PLAYER = I.he
                async with WAITER(pid=WAITER.wid('compare')) as w:
                    AB = I.game.compare(he.ans, info['myguess'])
                    result = cfg.result.format(info["myguess"], AB)
                    I.updateHistry(result)
                    info['result'] = result.replace('display:block', '')  # 給前端slidedown用
                    if I.game.winner:
                        info[cfg.const.winner] = int(I is I.game.winner)
                    else:
                        if AB == cfg.const.bingo:
                            info[cfg.const.winner] = 1
                            I.game.winner = I
                            I.game.start = get_now_tw()#datetime.now()
            # ___________________________________________________
            await websocket.send_text(json.dumps(info))
    except Exception as e:
        print(e)


async def wsgame(websocket: WebSocket):
    '''main區域更新'''
    await websocket.accept()
    #
    try:
        while 1:
            await asyncio.sleep(cfg.wsgameCycle)
            #
            async with WAITER(pid=WAITER.wid(cfg.const.wsgame)) as w:
                domstr = cfg.const.default
                if GAME.players:
                    I = await PLAYER.creat()  # pid==''，不會跟w打架
                    dom = pq(resByI(I, 1, 1))
                    domstr = dom.find('#' + cfg.const.joingame).outerHtml()  # 傳送缺對手的game
                # --------------------------------------------------
                await websocket.send_text(domstr)
                ans = await websocket.receive_text()  # 等待三種前端畫面
                # --------------------------------------------------
                # (1)非玩家index _________________________________
                if cfg.const.newgame in ans:
                    continue
                # (2)p1等待中 _________________________________
                if cfg.const.p1waiting in ans:
                    _, gid, left = ans.split(cfg.const.at)
                    g: GAME = GAME.games.get(gid)
                    # 兩種畫面變化: 非玩家index or 對戰畫面
                    if int(left) <= 0.5 or not g:
                        if g:
                            g.leavegames()
                        I = await PLAYER.creat()
                        dom = pq(resByI(I, 1, 1))
                        domstr = dom.find('#' + cfg.const.main).html()
                        # ________________<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        await websocket.send_text(domstr)
                        # w.leavemyg(wsdisconnect=True, msg=cfg.const.stopwait)  # 前端F5
                    elif g and g.p2:
                        I: PLAYER = g.p1
                        dom = pq(resByI(I, 1, 1))
                        domstr = dom.find('#' + cfg.const.main).html()
                        # ________________<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        await websocket.send_text(domstr)
                    #
                    continue
                # (3) 對戰畫面 _________________________________
                if cfg.const.p12vs in ans:
                    _, pno, gid, left = ans.split(cfg.const.at)
                    g: GAME = GAME.games.get(gid, None)
                    # 兩種畫面變化: 非玩家index or 更新histry
                    if int(left) <= 0.5 or not g:
                        if g:
                            g.leavegames()
                        I = await PLAYER.creat()
                        dom = pq(resByI(I, 1, 1))
                        domstr = dom.find('#' + cfg.const.main).html()
                        # ________________<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        await websocket.send_text(domstr)
                        # w.leavemyg(wsdisconnect=True, msg=cfg.const.stopgame)  # 前端F5
                    else:
                        if (winner := g.winner):
                            result = f'{cfg.const.winner}:{winner.pname}'
                        else:
                            I: PLAYER = GAME.players.get(pno + cfg.const.at + gid)
                            he: PLAYER = I.he
                            if he.pname == cfg.const.ai:
                                # 給AI猜一次
                                aiguess = he.aiguess()
                                AB = he.game.compare(I.ans, aiguess)
                                result = cfg.result.format(aiguess, AB)
                                he.updateHistry(result)
                                if AB == cfg.const.bingo:
                                    g.winner = he
                                    g.start = get_now_tw()#datetime.now() 
                                    #
                                    # print(he.histry)
                                    savetos3(I.ans, he.histry)
                            #
                            result = he.histry
                        # ________________<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                        await websocket.send_text(result)
                        await websocket.receive_text()  # 多收一次加速前端onmessage
    except Exception as e:
        print(e)
