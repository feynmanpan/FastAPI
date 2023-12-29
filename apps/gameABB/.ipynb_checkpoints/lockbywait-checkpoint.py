from types import SimpleNamespace
import asyncio
import uuid
import re
from enum import Enum
from typing import Union
from fastapi import WebSocketDisconnect
################################################################


class WAITER:
    '''
        排到第一才取得獨佔權
        gn = WAITER.gns.players
        pid = '222'
        async with WAITER(gn, pid) as w:
            # 排到第一
            print(w.__dict__)
            print(w.waiters[gn].keys())
        #
        print(w.waiters[gn].keys())
    '''
    _gns = ['players', 'games']
    gns = SimpleNamespace(**dict(zip(_gns, _gns)))
    gn = gns.players  # 所屬群名
    pid = ''  # 用來等待的字串
    myg = {}  # 所屬群 {pid:self}
    # 分為兩群等待者
    waiters = {gn: {} for gn in _gns}  # {gn:{pid:self}}
    # ______________________________________________________________

    def __new__(cls, gn: str = gn, pid: str = pid):
        '''在指定群gn尋找自己'''
        gn = (gn in cls._gns) and gn or cls.gn
        myg = cls.waiters[gn]
        #
        if not (self := myg.get(pid)):
            self = object.__new__(cls)
            self.gn = gn
            self.pid = pid or self.wid()
            self.myg = myg
            self.myg[pid] = self
        #
        return self

    async def becomeFirst(self) -> None:
        while (self.pid in self.myg) and self.pid != list(self.myg.keys())[0]:
            await asyncio.sleep(0.5)

    @staticmethod
    def wid(prefix='') -> str:
        sep = prefix and '_' or ''
        return prefix + sep + uuid.uuid4().hex.upper()

    def leavemyg(self, wsdisconnect=False):
        if self.pid in self.myg:
            del self.myg[self.pid]
        if wsdisconnect:
            raise WebSocketDisconnect
    # ______________________________________________________________

    async def __aenter__(self):
        '''進入 async with，直到第一等待，回傳self'''
        await self.becomeFirst()
        return self

    async def __aexit__(self, ex_type, ex_value, ex_traceback) -> None:
        '''離開 async with，離開waiters'''
        self.leavemyg()
