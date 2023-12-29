import aiohttp
import asyncio
from collections import namedtuple
from pyquery import PyQuery as pq
##################################################


class LOTTERY:
    cols = [
        'name',
        'no', 'ymd', 'area1', 'area1_asc', 'area2'
    ]
    #
    y_start = 103
    m_start = 1
    #
    _names = ['super', 'big', 'today']
    names = namedtuple('types', _names)(*_names)
    #
    url_home = 'https://www.taiwanlottery.com.tw'
    urls_history = {
        names.super: f"{url_home}/lotto/superlotto638/history.aspx",
        names.big: f"{url_home}/lotto/Lotto649/history.aspx",
        names.today: f"{url_home}/lotto/DailyCash/history.aspx",
    }
    #
    _ss = dict.fromkeys(_names, None)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    }
    timeout = 30
    last_threevars = None
    # ___________________________________________________-

    def __init__(self, name=names.super):
        self.name = name
        self.url_history = self.urls_history[name]
        self.row = dict.fromkeys(self.cols, None)

    @property
    def ss(self) -> aiohttp.ClientSession:
        '''各name用自己的session'''
        if not self._ss.get(self.name):
            connector = aiohttp.TCPConnector(ssl=True, limit=100)
            TO = aiohttp.ClientTimeout(total=self.timeout)
            self._ss[self.name] = aiohttp.ClientSession(connector=connector, timeout=TO)
        #
        return self._ss[self.name]

    def set_threevars(self, rtext: str):
        doc = pq(rtext, parser='html')
        vs = doc.find("#__VIEWSTATE").val()
        vsg = doc.find("#__VIEWSTATEGENERATOR").val()
        ev = doc.find("#__EVENTVALIDATION").val()
        if vs and vsg and ev:
            self.last_threevars = vs, vsg, ev

    async def first_get(self):
        async with self.ss.get(self.url_history, headers=self.headers, proxy=None) as r:
            if (status := r.status) == 200:
                rtext = await r.text(encoding='utf8')
                if rtext:
                    self.set_threevars(rtext)
                    return rtext

    async def post(self, y=y_start, m=m_start):
        while not self.last_threevars:
            await self.first_get()
            await asyncio.sleep(0.5)
        #
        payload = {
            "__VIEWSTATE": self.last_threevars[0],
            "__VIEWSTATEGENERATOR": self.last_threevars[1],
            "__EVENTVALIDATION": self.last_threevars[2],
            "forma": "請選擇遊戲",
            "SuperLotto638Control_history1$txtNO": "",
            "SuperLotto638Control_history1$chk": "radYM",
            "SuperLotto638Control_history1$dropYear": y,
            "SuperLotto638Control_history1$dropMonth": m,
            "SuperLotto638Control_history1$btnSubmit": "查詢",
        }
        async with self.ss.post(self.url_history, headers=self.headers, proxy=None, data=payload) as r:
            if r.status == 200:
                rtext = await r.text(encoding='utf8')
                if rtext:
                    self.set_threevars(rtext)
                    return rtext