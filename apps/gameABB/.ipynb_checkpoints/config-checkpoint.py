import os
from enum import Enum
import json
from itertools import combinations as cb
#
from fastapi.templating import Jinja2Templates
from utils import CONST_BASE
import pandas as pd
#
##########################################################
cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
#
games_maxN = 100  # game數量上限
cleanGamesCycle = 3 * 1  # 協程每幾秒清一次
durationMax = 120  # 允許game存活幾秒
durationMax_winner = 10  # 產生winner後允許game存活幾秒
wsgameCycle = 1  # websocket while週期
#
aiguess_all = set('0123456789')
pname_pattern = '^[a-z0-9]{1,10}$'
ans_digits = 4
ans_pattern = '^[0-9]{4}$'
histry_pattern = '([0-9]{4})➜(.)A(.)B'
histry_begin = '<span class="guess" style="display:block">begin</span>'
result = histry_begin.replace('begin', '{}➜{}')
pattern_2A2B = '(....)➜2A2B'
swap_index_2A2B = list(cb(range(ans_digits), 2))
# _________________________________________________


class MSG(Enum):
    '''I.msg'''
    isPlayer = '已是玩家'
    #
    needpnameans = '請提供正確格式之暱稱及答案'
    pnameisused = '暱稱{pname}已有人使用，請重新取名'
    #
    joinsuccess = 'p2加入成功'
    joinfail = 'p2已被搶'
    #
    newgamesuccess = '開新局成功'
    newgamefail = '目前遊戲局數已達上限，請稍候'


class const(CONST_BASE):
    '''給前端用的常數'''
    main: str
    newgame: str
    joingame: str
    p1waiting: str
    p12vs: str
    infoarea: str
    card: str
    leftsec: str
    #
    pid: str
    pname: str
    ans: str
    gid: str
    #
    newjoin: str
    checkans: str
    #
    at = '@'
    histry_begin = json.dumps(histry_begin).strip('"')  # '<span class=\\"guess\\" style=\\"display: block;\\">begin</span>'
    #
    #DNS = "wss://wtb.ddns.net:6001"
    DNS = "wss://abb.aws360.net"
    #DNS = "wss://54.249.153.34"
    wsself: str
    wsgame: str
    default: str
    winner: str
    bingo = '4A0B'
    durationMax_winner = durationMax_winner
    wsgameCycle = wsgameCycle
    #
    domstr_main: str
    domstr_infoarea: str
    #
    ai = 'ai'
    isAI = 'isAI'
    histry_strlimit = 472 + 514 + 522
    #
    stopwait = 'p1取消等待'
    stopgame = 'p12取消對戰'
    #
