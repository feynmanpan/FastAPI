'''1A2B的遊戲邏輯'''
import asyncio
from typing import Union, Dict, Any
import uuid
from enum import Enum
import re
import datetime as dt
from datetime import datetime, timezone
import time, pytz
from fastapi import Request
import json
from random import sample, shuffle, choice
from itertools import permutations
#
from apps.gameABB.lockbywait import WAITER
import apps.gameABB.config as cfg
################################################################
def get_now_tw():
    tw = pytz.timezone("Asia/Taipei")
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    now_tw = tw.normalize(now_utc.astimezone(tw))
    #
    return now_tw


class MAN:
    pid = ""
    pname = ""
    ans = ""
    pno = ""
    gid = ""
    req = Request(scope={"type": "http"})
    info = {}
    isPlayer = False
    he = None
    #
    MSG = cfg.MSG
    at = cfg.const.at
    #
    aiguess_all = cfg.aiguess_all
    aiguess_exclude = set()  # A+B=0 全部都不要的
    aiguess_bingo_list = []


class GAME:
    games_maxN = cfg.games_maxN
    games: Dict[str, Any] = {}  # {gid:game} 所有game
    players: Dict[str, MAN] = {}  # {pid:player} 所有在game中的玩家
    #
    cleanGames_cnt = 0
    cleanGamesCycle = cfg.cleanGamesCycle  # 協程每幾秒清一次
    durationMax = cfg.durationMax  # 允許game存活幾秒
    durationMax_winner = cfg.durationMax_winner
    # ____________________________________________________________

    def __init__(
        self, gid: str = "", p1: Union[MAN, None] = None, p2: Union[MAN, None] = None
    ) -> None:
        self.gid = gid
        self.p1 = p1
        self.p2 = p2
        self.winner: Union[MAN, None] = None
        # 紀錄games, players
        self.games[gid] = self
        if p1:
            self.players[p1.pid] = p1
        if p2:
            self.players[p2.pid] = p2
        # 記錄開局時間
        self.start = get_now_tw()  # datetime.now()

    # ______________________________________________________________

    def getPbyPno(self, pno: str = "1") -> MAN:
        return pno == "1" and self.p1 or self.p2

    def getHisPno(self, mypno: str = "1") -> str:
        return "12".replace(mypno, "")

    def getHe(self, mypno: str = "1") -> MAN:
        return self.getPbyPno(self.getHisPno(mypno))

    def leavegames(self):
        if self.gid in self.games:
            if self.p1 and self.p1.pid in self.players:
                del self.players[self.p1.pid]
            if self.p2 and self.p2.pid in self.players:
                del self.players[self.p2.pid]
            self.p1 = None
            self.p2 = None
            del self.games[self.gid]

    def addP2(self, p2: Union[MAN, None]):
        if p2:
            self.p2 = p2
            self.players[p2.pid] = p2
            # 互記he
            self.p1.he = self.p2
            self.p2.he = self.p1
            self.start = get_now_tw()  # datetime.now()

    @property
    def duration(self) -> int:
        """開局至今的秒數"""
        # D = datetime.now() - self.start
        D = get_now_tw() - self.start
        return int(D.total_seconds())

    @property
    def cntP12(self) -> int:
        return (self.p1 != None) + (self.p2 != None)

    @staticmethod
    def compare(ans: str, guess: str) -> str:
        """計算兩組數字幾A幾B"""
        A, B = 0, 0
        for idx, c in enumerate(guess):
            if c == ans[idx]:  # 數字及位置都正確
                A += 1
            elif c in ans:  # 只有數字正確
                B += 1
        #
        return f"{A}A{B}B"

    @classmethod
    async def cleanGames(cls):
        # cleanGames_cnt = 0
        if cls.cleanGames_cnt:
            return
        # print('cleanGames START+++++++++++++++++++++==')
        while 1:
            cls.cleanGames_cnt = 1
            await asyncio.sleep(cls.cleanGamesCycle)
            # print(f'\n開始第{cleanGames_cnt}次清除逾時game，durationMax={cls.durationMax}')
            async with WAITER(pid="cleanGames") as w:  # 必須排隊，以免games數量變化
                try:
                    for g in list(cls.games.values()):
                        dmax = g.winner and cls.durationMax_winner or cls.durationMax
                        if g.duration >= dmax:
                            g.leavegames()
                    # 一場等人的遊戲都沒有，新增AI玩家
                    if not [g for g in cls.games.values() if not g.p2]:
                        AI = await PLAYER.creat(isAI=1)
                except Exception:
                    w.leavemyg()


##############################################################
# print(__name__)
asyncio.create_task(GAME.cleanGames())
##############################################################


class PLAYER(MAN):
    """實際用creat去造實體
    I = await PLAYER.creat(pid=pid,pname=pname,ans=ans,gid=gid)
    """

    GAME = GAME  # 模板需要，非玩家的I要用來查join
    const = cfg.const  # 模板用
    constjson = cfg.const.jsonstr  # 模板 js 用
    #
    pname_pattern = cfg.pname_pattern
    ans_pattern = cfg.ans_pattern
    #
    pid = ""
    pname = ""
    ans = ""
    pno = ""
    gid = ""
    game: Union[GAME, None] = None
    he: Union[MAN, None] = None
    #
    msg = ""
    histry_begin = cfg.histry_begin
    histry = ""
    # ______________________________________________________________

    def __new__(cls, **init):
        """四種結果
        A.已經是p1/p2
        B.檢查pname,ans格式不通過(或沒有給)
        C.準備成為p1
        D.準備成為p2
        """
        # A.已經是p1或p2
        pid = init.get("pid", "")  # pid='pno@gid' '1@CD833297650C4D1BAE27D9193CF58C45'
        if self := GAME.players.get(pid):
            return self
        # 不是player，準備成為p1,p2
        self = object.__new__(cls)
        # B.檢查格式不過時，都用預設屬性值
        pname = init.get("pname", "").lower()
        ans = init.get("ans", "")
        allans = ["".join(e) for e in permutations("0123456789", 4)]
        allans_g1234 = [
            [
                a,
                GAME.compare(a, "1234")
                + GAME.compare(a, "5678")
                + GAME.compare(a, "1590")
                + GAME.compare(a, "1357"),
            ]
            for a in allans
        ]
        #
        if not cls.checkPnameAns(pname, ans):
            self.histry = self.histry_begin
            self.aiguess_all = cfg.aiguess_all
            self.aiguess_exclude = set()  # A+B=0 全部都不要的
            self.aiguess_bingo_list = []
            self.allans = allans[:]
            self.allans_g1234 = allans_g1234[:]
            return self
        # CD.根據gid判斷p1或p2，p1 new game，或p2 join game
        gid = init.get("gid", "")
        game = GAME.games.get(gid)  # p2打算join的game
        gid = game and gid or ""
        #
        self.pid = self.newPid(gid)  # p2會沿用gid
        self.pname = pname
        self.ans = ans
        self.pno = self.pid[0]
        self.gid = self.pid[2:]
        self.game = game
        self.req = init.get("req", self.req)
        self.histry = self.histry_begin
        #
        self.aiguess_all = cfg.aiguess_all
        self.aiguess_exclude = set()  # A+B=0 全部都不要的
        self.aiguess_bingo_list = []
        self.allans = allans[:]
        self.allans_g1234 = allans_g1234[:]
        #
        return self

    @classmethod
    async def creat(cls, **init) -> MAN:
        """
        I = await PLAYER.creat(pid=pid,pname=pname,ans=ans,gid=gid)
        根據init四個參數產生一個user
        """
        if isAI := init.get(cfg.const.isAI, 0):
            init[cfg.const.pname] = cfg.const.ai
            init[cfg.const.ans] = cls.randomsample()
            init["gn"] = WAITER.gns.games

        self = cls(**init)
        # A.已是p1,p2 ___________________________________________
        if self.isPlayer:
            self.msg = self.MSG.isPlayer.value
            return self
        # B.pname ans格式不通過(或沒有給) ___________________________________________
        if self.pid == "":
            self.msg = self.MSG.needpnameans.value
            return self
        # CD.檢查pname是否重複/p1檢查局數/p2 join
        async with WAITER(gn=init.get("gn", ""), pid=self.pid) as w:
            try:
                # pname是否重複，AI可重複 ___________________________________________
                if (not isAI) and self.pname in [
                    p.pname for p in GAME.players.values()
                ]:
                    self.msg = self.MSG.pnameisused.value.format(pname=self.pname)
                    return self
                # p2 join game ___________________________________________
                if self.game:
                    if self.game.p2 is None:
                        self.game.addP2(self)
                        self.msg = self.MSG.joinsuccess.value
                    else:
                        self.msg = self.MSG.joinfail.value
                    #
                    return self
                # p1 new game ___________________________________________
                for _ in range(5):
                    if len(GAME.games) >= GAME.games_maxN:
                        await asyncio.sleep(0.5)
                    else:
                        self.game = GAME(gid=self.gid, p1=self, p2=None)
                        self.msg = self.MSG.newgamesuccess.value
                        break
                else:
                    self.msg = self.MSG.newgamefail.value
                return self
            except Exception:
                w.leavemyg()
                return self

    @property
    def isPlayer(self) -> bool:
        return self.pid in GAME.players

    @property
    def info(self) -> dict:
        info = {
            "games": list(GAME.games),
            "players": [f"{p.pid}_{p.pname}/{p.ans}" for p in GAME.players.values()],
            "waiters": list(WAITER.waiters["players"]),
            #
            "I": {
                "isPlayer": self.isPlayer,
                "pid": self.pid,
                "pname": self.pname,
                "ans": self.ans,
                "pno": self.pno,
                "gid": self.gid,
                "msg": self.msg,
            },
        }
        return info

    def newPid(self, gid: str = "") -> str:
        """根據gid區分1,2玩家"""
        if gid:
            pid = "2" + self.at + gid
        else:
            pid = "1" + self.at + uuid.uuid4().hex.upper()
        return pid

    def updateHistry(self, result="") -> str:
        """更新玩家猜測歷史"""
        self.histry = (
            result + self.histry
        )  # .replace(cfg.histry_begin, "") + cfg.histry_begin
        return self.histry

    @classmethod
    def checkPnameAns(cls, pname: str = "", ans: str = "") -> bool:
        """檢查格式
        pname須為1-10位英數
        ans須為4位相異數字
        """
        if not pname or not ans:
            return False
        # pname
        if not re.match(cls.pname_pattern, pname):
            return False
        # ans
        if not re.match(cls.ans_pattern, ans):
            return False
        for c in ans:
            if ans.count(c) > 1:
                return False
        #
        return True

    @staticmethod
    def randomsample(U=range(10), digits=cfg.ans_digits) -> str:
        ans = ""
        if digits and len(U) >= digits:
            ans = "".join(str(n) for n in sample(list(U), digits))
        return ans

    def update_allans(self) -> str:
        """暴力排除法"""
        histry = re.findall(cfg.histry_pattern, self.histry)
        #
        if len(histry) == 4 and 0:
            g1234 = "".join(f"{A}A{B}B" for guess_str, A, B in histry[::-1])
            self.allans = [e[0] for e in self.allans_g1234 if e[1] == g1234]
            # print('g1234=',g1234,len(self.allans ))
        if len(histry) <=5:
            tmp = []
            for a in self.allans:
                for guess_str, A, B in histry:                    
                    if GAME.compare(a, guess_str) != f'{A}A{B}B':
                        break
                else:
                    tmp.append(a) # 所有guess_str重猜 a 都吻合既有的A,B 才加入可能答案
            #
            self.allans = tmp

        #
        for guess_str, A, B in histry:
            guess = set(guess_str)  # - self.aiguess_exclude
            g1 = guess_str[0]
            g2 = guess_str[1]
            g3 = guess_str[2]
            g4 = guess_str[3]
            A = int(A)
            B = int(B)
            sumAB = A + B
            # 交集數量相同，不重複
            self.allans = [
                e
                for e in self.allans
                if len(set(e) & guess) == sumAB and e != guess_str
            ]
            #
            if A == 0 and B == 1:
                self.allans = [
                    e
                    for e in self.allans
                    if e[0] != g1 and e[1] != g2 and e[2] != g3 and e[3] != g4
                ]
            if A == 1 and B == 0:
                self.allans = [
                    e
                    for e in self.allans
                    if e[0] == g1 or e[1] == g2 or e[2] == g3 or e[3] == g4
                ]
            if A == 0 and B == 2:
                tmp = []
                for e in self.allans:
                    u = list(set(e) & guess)
                    #
                    u1 = u[0]
                    u2 = u[1]
                    if e.index(u1) == guess_str.index(u1):
                        continue
                    if e.index(u2) == guess_str.index(u2):
                        continue
                    #
                    tmp.append(e)
                #
                self.allans = tmp
            if A == 2 and B == 0:
                tmp = []
                for e in self.allans:
                    u = list(set(e) & guess)
                    #
                    u1 = u[0]
                    u2 = u[1]
                    if e.index(u1) != guess_str.index(u1):
                        continue
                    if e.index(u2) != guess_str.index(u2):
                        continue
                    #
                    tmp.append(e)
                #
                self.allans = tmp
            if A == 0 and B == 3:
                tmp = []
                for e in self.allans:
                    u = list(set(e) & guess)
                    #
                    u1 = u[0]
                    u2 = u[1]
                    u3 = u[2]
                    if e.index(u1) == guess_str.index(u1):
                        continue
                    if e.index(u2) == guess_str.index(u2):
                        continue
                    if e.index(u3) == guess_str.index(u3):
                        continue
                    #
                    tmp.append(e)
                #
                self.allans = tmp
            if A == 3 and B == 0:
                tmp = []
                for e in self.allans:
                    u = list(set(e) & guess)
                    #
                    u1 = u[0]
                    u2 = u[1]
                    u3 = u[2]
                    if e.index(u1) != guess_str.index(u1):
                        continue
                    if e.index(u2) != guess_str.index(u2):
                        continue
                    if e.index(u3) != guess_str.index(u3):
                        continue
                    #
                    tmp.append(e)
                #
                self.allans = tmp
            if A == 0 and B == 4:
                tmp = []
                for e in self.allans:
                    u = list(set(e) & guess)
                    #
                    u1 = u[0]
                    u2 = u[1]
                    u3 = u[2]
                    u4 = u[3]
                    if e.index(u1) == guess_str.index(u1):
                        continue
                    if e.index(u2) == guess_str.index(u2):
                        continue
                    if e.index(u3) == guess_str.index(u3):
                        continue
                    if e.index(u4) == guess_str.index(u4):
                        continue
                    #
                    tmp.append(e)
                #
                self.allans = tmp
            # print(guess_str, len(self.allans))

    def aiguess(self) -> str:
        """AI猜測邏輯"""
        #
        histry = re.findall(cfg.histry_pattern, self.histry)

        # (1)
        # if not histry:
        #     first = self.randomsample()
        #     return first
        if (cnt := len(histry)) < 4 and 0:
            return ["1234", "5678", "1590", "1357"][cnt]

        #
        self.update_allans()
        # print("self.allans = ", len(self.allans))
        return sample(self.allans, 1)[0]
        # (2)
        if self.aiguess_bingo_list:
            if guess_2A2Bs := re.findall(cfg.pattern_2A2B, self.histry):
                guess_2A2B = list(guess_2A2Bs[-1])
                for i, j in cfg.swap_index_2A2B:
                    guess_2A2Bc = guess_2A2B[:]
                    guess_2A2Bc[i], guess_2A2Bc[j] = guess_2A2Bc[j], guess_2A2Bc[i]
                    guess_str = "".join(guess_2A2Bc)
                    if (
                        guess_str not in self.histry
                        and guess_str in self.aiguess_bingo_list
                    ):
                        self.aiguess_bingo_list.remove(guess_str)
                        return guess_str
            return self.aiguess_bingo_list.pop(0)
        # (3)
        aiguess_include = set(self.aiguess_all)  # 有價值的數字集合
        aiguess_include_min = 4  # 準備從有價值集合中取樣的數量
        #
        for guess_str, A, B in histry:
            guess = set(guess_str)  # - self.aiguess_exclude
            A = int(A)
            B = int(B)
            sumAB = A + B
            if sumAB == 0:
                self.aiguess_exclude |= guess
                aiguess_include -= self.aiguess_exclude
                if len(self.aiguess_exclude) > 4:
                    break
                else:
                    continue
            if sumAB == 1:
                aiguess_include = guess  # 只有一個對，故意猜三個錯，加速產生0A0B
                aiguess_include_min = 3  # min(3, len(aiguess_include))
                break
            if sumAB in [2, 3]:
                aiguess_include = guess
                aiguess_include -= self.aiguess_exclude
                aiguess_include_min = sumAB  # min(sumAB, len(aiguess_include))
                break
            if sumAB == 4:
                self.aiguess_bingo_list = ["".join(p) for p in permutations(guess_str)]
                self.aiguess_bingo_list.remove(guess_str)
                shuffle(self.aiguess_bingo_list)
                break
        # (4) A+B=4
        if self.aiguess_bingo_list:
            return self.aiguess_bingo_list.pop(0)
        # (5)
        u1 = aiguess_include
        u2 = self.aiguess_all - u1 - self.aiguess_exclude
        #
        guessA = self.randomsample(u1, aiguess_include_min)
        guessB = self.randomsample(u2, cfg.ans_digits - aiguess_include_min)
        final = self.randomsample(guessA + guessB)
        #
        return final