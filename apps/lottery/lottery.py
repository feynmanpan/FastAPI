import aiohttp
import asyncio
from collections import namedtuple
from types import SimpleNamespace
from pyquery import PyQuery as pq
from typing import Union
from datetime import datetime
import sqlalchemy as sa
import pandas as pd
import random
#
from apps.sql.config import dbwtb
import apps.ips.config as ipscfg
from apps.lottery.model import LOTTO
##################################################


class LOTTERY:
    '''抓樂透'''
    cols = [
        'name',
        'no', 'ymd', 'area1', 'area1asc', 'area2',
        'salesamount', 'totalbonus',
    ]
    #
    y_start = 103
    m_start = 1
    #
    _names = ['super', 'big', 'today']
    names = namedtuple('types', _names)(*_names)  # daily_get_lottery 有需要for
    # names = SimpleNamespace(**dict(zip(_names, _names)))
    #
    url_home = 'https://www.taiwanlottery.com.tw'
    urls_history = {
        names.super: f"{url_home}/lotto/superlotto638/history.aspx",
        names.big: f"{url_home}/lotto/Lotto649/history.aspx",
        names.today: f"{url_home}/lotto/DailyCash/history.aspx",
    }
    #
    _ss = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    }
    timeout = 60
    # last_threevars = None
    payloads = {
        names.super: {
            "__VIEWSTATE": "",
            "__VIEWSTATEGENERATOR": "",
            "__EVENTVALIDATION": "",
            "forma": "請選擇遊戲",
            "SuperLotto638Control_history1$txtNO": "",
            "SuperLotto638Control_history1$chk": "radYM",
            "SuperLotto638Control_history1$dropYear": "",
            "SuperLotto638Control_history1$dropMonth": "",
            "SuperLotto638Control_history1$btnSubmit": "查詢",
        },
        names.big: {
            "__VIEWSTATE": "",
            "__VIEWSTATEGENERATOR": "",
            "__EVENTVALIDATION": "",
            "forma": "請選擇遊戲",
            "Lotto649Control_history$txtNO": "",
            "Lotto649Control_history$chk": "radYM",
            "Lotto649Control_history$dropYear": "",
            "Lotto649Control_history$dropMonth": "",
            "Lotto649Control_history$btnSubmit": "查詢",
        },
        names.today: {
            "__VIEWSTATE": "",
            "__VIEWSTATEGENERATOR": "",
            "__EVENTVALIDATION": "",
            "forma": "請選擇遊戲",
            "D539Control_history1$txtNO:": "",
            "D539Control_history1$chk": "radYM",
            "D539Control_history1$dropYear": "",
            "D539Control_history1$dropMonth": "",
            "D539Control_history1$btnSubmit": "查詢",
        },
    }
    seq = {
        names.super: [
            [1, 4, 5, 17], ["SuperLotto638Control_history1_dlQuery_SNo", "SuperLotto638Control_history1_dlQuery_No"]
        ],
        names.big: [
            [1, 3, 4, 17], ["Lotto649Control_history_dlQuery_SNo", "Lotto649Control_history_dlQuery_No"]
        ],
        names.today: [
            [1, 1, 2, 14], ["D539Control_history1_dlQuery_SNo", "D539Control_history1_dlQuery_No"]
        ]
    }
    #
    dt_format = "%Y-%m-%d_%H:%M:%S"
    nodata = ['查無資料', '您要尋找的資源有問題而無法顯示']
    # ___________________________________________________-

    def __init__(self, name=names.super):
        self.name = name
        self.url_history = self.urls_history[name]
        self.ymdata = []
        self.last_threevars = None
        self._proxy = None

    @property
    def ss(self) -> aiohttp.ClientSession:
        '''各name用自己的session'''
        if not self._ss.get(self.name, None):
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

    @property
    async def proxy(self):
        # if not self._proxy:
        #     if ippt := await ipscfg.ips_Queue.get():
        #         self._proxy = f"http://{ippt['ip']}:{ippt['port']}"
        return self._proxy

    async def first_get(self) -> Union[str, None]:
        '''進入某獎項的頁面'''
        self.last_threevars = None
        self._proxy = None
        proxy = await self.proxy
        async with self.ss.get(self.url_history, headers=self.headers, proxy=proxy) as r:
            if (status := r.status) == 200:
                rtext = await r.text(encoding='utf8')
                if rtext:
                    self.set_threevars(rtext)
                    return rtext

    async def post(self, y=y_start, m=m_start) -> Union[str, None]:
        '''針對某年某月送出查詢'''
        while not self.last_threevars:
            await self.first_get()
            await asyncio.sleep(0.5)
        #
        payload = {} | self.payloads[self.name]
        for k in payload:
            if k == "__VIEWSTATE":
                payload[k] = self.last_threevars[0]
            elif k == "__VIEWSTATEGENERATOR":
                payload[k] = self.last_threevars[1]
            elif k == "__EVENTVALIDATION":
                payload[k] = self.last_threevars[2]
            elif "dropYear" in k:
                payload[k] = y
            elif "dropMonth" in k:
                payload[k] = m

        async with self.ss.post(
                self.url_history, headers=self.headers,
                proxy=await self.proxy, data=payload,
        ) as r:
            if r.status == 200:
                try:
                    rtext = await r.text(encoding='utf8')
                    if rtext:
                        self.set_threevars(rtext)
                        if self.nodata[0] in rtext:
                            return self.nodata[0]
                        else:
                            return rtext
                except Exception as e:
                    rtext = await r.text()
                    if self.nodata[1] in rtext:
                        return self.nodata[1]

    async def get_ymdata(self, y=y_start, m=m_start) -> list:
        '''抓取某年某月的多筆開獎結果'''
        self.ymdata = []  # 先清空
        # 月初可能查無資料
        if rtext := await self.post(y=y, m=m):
            if rtext in self.nodata:
                self.ymdata.append(rtext)
            else:
                doc = pq(rtext, parser='html')
                #
                if len(doc.find('.table_org.td_hm')) + len(doc.find('.table_gre.td_hm')):
                    seq = self.seq
                    #
                    a, b, c = seq[self.name][0][0], seq[self.name][0][1], seq[self.name][0][2]
                    d, e = seq[self.name][1][0], seq[self.name][1][1]
                    f = seq[self.name][0][3]
                    create_dt = datetime.today().strftime(self.dt_format)
                    #
                    for tbcls in ['.table_org.td_hm', '.table_gre.td_hm']:
                        for tb in doc.find(tbcls):
                            trs = pq(tb).find("tr")
                            tra = trs.eq(a)
                            trb = trs.eq(b)
                            trc = trs.eq(c)
                            # __________________________________________________________
                            no = tra.find("span").eq(0).text()
                            ymd = tra.find("span").eq(1).text()
                            area1 = trb.find(f"span[id*='{d}']").text().__str__().replace(" ", '_')[:f]  # 一次多個span的text
                            area1_asc = trc.find(f"span[id*='{e}']").text().__str__().replace(" ", '_')[:f]  # 一次多個span的text
                            # area2, 銷售金額，獎金總額 __________________________________________________________
                            if self.name != self.names.today:
                                area2 = trc.find("span").eq(-1).text()
                                #
                                salesamount = int(tra.find("span[id*='SellAmount']").eq(0).text().__str__().replace(",", ''))
                                totalbonus = int(tra.find("span[id*='Total']").eq(0).text().__str__().replace(",", ''))
                            else:
                                area2 = None
                                #
                                trd = trs.eq(4)
                                salesamount = int(trd.find("span[id*='TotalAmount']").eq(0).text().__str__().replace(",", ''))
                                totalbonus = int(trd.find("span[id*='Jackpot']").eq(0).text().__str__().replace(",", ''))
                            # 存 DB __________________________________________________________
                            row = dict(zip(self.cols, [self.name, no, ymd, area1, area1_asc, area2, salesamount, totalbonus]))
                            row['create_dt'] = create_dt
                            self.ymdata.append(row)
                    #
                    sorted(self.ymdata, key=lambda row: row['no'], reverse=True)
        #
        return self.ymdata

    async def single_insert(self, db=dbwtb, tb=LOTTO, row={}) -> Union[int, None]:
        '''單筆插入'''
        if row:
            cs = [tb.idx]
            w1 = tb.name == row['name']
            w2 = tb.no == row['no']
            w3 = tb.ymd == row['ymd']
            #
            query = sa.select(cs).where(w1).where(w2).where(w3)
            rows = await db.fetch_all(query)
            # DB沒有才插入
            if not rows:
                query = sa.insert(tb).values(**row)
                await db.execute(query)
                # print(f'插入{row["ymd"]}的開獎資料')
                return 1

    async def bulk_insert(self, db=dbwtb, tb=LOTTO) -> Union[int, None]:
        '''多筆異步插入'''
        if self.ymdata:
            tasks = [asyncio.create_task(self.single_insert(db, tb, r)) for r in self.ymdata]
            # await asyncio.wait(tasks)
            count = sum([p for p in await asyncio.gather(*tasks) if p])
            print(f"插入{count}筆資料: {self.ymdata[0]['name']}_{self.ymdata[0]['ymd']}")
            return count

    async def get_maxymd(self, db=dbwtb, tb=LOTTO) -> Union[str, None]:
        '''確認已抓的最後日期'''
        cs = [sa.func.max(tb.ymd)]
        w1 = tb.name == self.name
        #
        query = sa.select(cs).where(w1)
        rows = await db.fetch_all(query)
        # 103/01/31
        return rows and rows[0]['max_1'] or None

    async def get_ymrange(self, db=dbwtb, tb=LOTTO) -> list:
        '''從DB最後一個月開始抓到本月'''
        maxymd = await self.get_maxymd(db=db, tb=tb)
        if not maxymd:
            y_start = self.y_start
            m_start = self.m_start
        else:
            # 最新一個月重抓一次
            y_start = int(maxymd[:3])
            m_start = int(maxymd[4:6])
        #
        y_end = datetime.today().year
        m_end = datetime.today().month
        #
        sd = f'{y_start+1911}-{m_start:02}-01'
        ed = f'{y_end}-{m_end:02}-01'
        yms = pd.date_range(start=sd, end=ed, freq='MS').astype(str).tolist()
        #
        return [(int(ymd[:4]) - 1911, int(ymd[5:7])) for ymd in yms]

    async def getdata_in_ymrange(self):
        '''對yms中的多個年月進行爬蟲'''
        yms = await self.get_ymrange()
        for y, m in yms:
            await asyncio.sleep(0.5 + random.uniform(0, 3.5))
            #
            print(f'{self.name:<5}: 開始抓{y}-{m}的開獎資料')
            while not (tmp := await self.get_ymdata(y=y, m=m)):
                print('\n' * 3 + f'{self.name:<5}: 重抓{y}-{m}的開獎資料' + '*' * 40 + '\n' * 3)
                self.last_threevars = None
                await asyncio.sleep(random.uniform(0, 4))
            # 抓到才下個月
            if isinstance(tmp[0], dict):
                await self.bulk_insert()
            else:
                # 有可能查無資料
                print(f'{y}-{m}: {tmp[0]}')
