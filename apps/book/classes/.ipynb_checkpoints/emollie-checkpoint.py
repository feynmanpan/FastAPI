# -*- coding: utf-8 -*-
from asyncio.tasks import create_task
import aiohttp
import aiofiles
import asyncio
import re
import json
import os
from pyquery import PyQuery as pq
from datetime import datetime
from time import time
from typing import Dict, Any, Callable, Awaitable, Coroutine, Optional, Union
from PIL import Image
import pytesseract
import copy
from copy import deepcopy
import itertools
import sqlalchemy as sa
from sqlalchemy import or_
import pandas as pd
#
from apps.sql.config import dbwtb
from apps.book.model import INFO
from apps.book.classes.abookbase import BOOKBASE
from apps.book.classes.bbooks import BOOKS
from apps.book.utils import write_file
from apps.book.config import q_size
#
import apps.ips.config as ipscfg
from apps.ips.config import headers


###################################################


class MOLLIE(BOOKBASE):
    '''茉莉'''
    info_default = {
        "bookid": "9789571345826",  # 大騙局
    }
    #
    bookid_pattern = BOOKBASE.isbn_pattern  # 茉莉的書號就以isbn為書號
    #
    url_search = 'http://www.mollie.com.tw/Mobile/Books.asp'
    search_OK = [
        '目前各分店皆無此書籍/影音商品',
        '因商品擺放於賣場，隨時會被售出',
    ]
    stock_sep = '_'
    stock_none = '查無此書'
    page_err = []
    #
    formdata = {
        'Action': 'BookSerach',
        'BookName': '',
        'Author': '',
        'Publisher': '',
        'BarCode': '',
        'XCHK': 'Y',
    }
    # __________________________________________________________

    def __init__(self, **init):
        # 書號=isbn
        is_isbn13 = len(self.bid) == 13
        init['isbn10'] = ((not is_isbn13) and self.bid) or None
        init['isbn13'] = (is_isbn13 and self.bid) or None
        #
        super().__init__(**init)

    async def update_info(self, proxy: Optional[str] = None, uid: Optional[int] = None, db=dbwtb):
        self._stime = time()
        # ======== 只留 uid=1 進行爬蟲，其他則等待及結束 =======
        if (uid := await super().update_info(uid=uid, proxy=proxy)) != 1:
            return self._update_result
        # ===================================================
        try:
            # 抓庫存資訊
            print('post 茉莉查詢頁面---------------------')
            #
            formdata = self.formdata | {'BarCode': self.bid}
            async with self.ss.post(self.url_search, headers=headers, proxy=self.now_proxy, data=formdata) as r:
                status = r.status
                rtext = (await r.text(encoding='big5')).replace('big5', 'utf8')
                #
                if status == 200 and rtext:
                    self._enter_bookpage = [s in rtext for s in self.search_OK]  # 要回傳有無庫存
        except asyncio.exceptions.TimeoutError as e:
            self._update['err'] = 'asyncio.exceptions.TimeoutError'
        except Exception as e:
            self._update['err'] = str(e)
        else:
            if (status == 200) and rtext and sum(self._enter_bookpage) == 1:
                # 確定有查詢結果
                print('bookpage_handle ---------------------')
                result = self.bookpage_handle(rtext)
                self.update_handle(result)
            else:
                self.page_err_handle(rtext, status)
        finally:
            return await self.update_final(uid=uid, db=db)

    def bookpage_handle(self, rtext) -> Dict[str, Any]:
        doc = pq(rtext, parser='html')
        td = doc.find("section#A table.table.table-bordered.text tr").eq(1).find('td').eq(0)
        # ________________________________________
        if self._enter_bookpage == [False, True]:
            title = td.find('span').eq(0).text().strip()
            stock = self.stock_sep.join(sorted(re.findall('..店', td.text().strip())))
        else:
            stock = self.stock_none
        #
        return locals()

    ##################  連續書號查詢 ##################

    @classmethod
    async def bid_cycle(cls):
        '''從博客來的isbn建立茉莉的書號'''
        #
        cls.BOOKS_bid_Cs = []
        no_rows_counter = 0
        no_rows_counter_max = 2000
        get_back = 10000
        #
        while 1:
            if cls.BOOKS_bid_Cs == [] or no_rows_counter > no_rows_counter_max:
                # 茉莉超前博客來 2000 個書號時，落後 get_back 個書號重新開始
                start_L = [s - get_back for s in BOOKS.start_L_new]
                if start_L[0] < 0:
                    start_L = BOOKS.start_L
                # 重造 BOOKS_bid_Cs
                cls.BOOKS_bid_Cs = [BOOKS.bid_cycle(prefix=p, digits=BOOKS.bid_digits, start=s) for s in start_L for p in BOOKS.bid_prefixes]
            ##########################################################
            # 從 BOOKS_bid_Cs 抓對應的ISBN
            cs = [INFO.isbn10, INFO.isbn13]
            w1 = INFO.store == 'BOOKS'
            w2 = INFO.err == None
            # 跟在博客來後面爬其 isbn
            bids = [next(C) for C in cls.BOOKS_bid_Cs]
            w3 = INFO.bookid.in_(bids)
            # 至少要有一種isbn
            w4 = or_(INFO.isbn10 != None, INFO.isbn13 != None)
            #
            query = sa.select(cs).where(w1 & w2 & w3).where(w4)
            rows = await dbwtb.fetch_all(query)
            if rows:
                df = pd.DataFrame(rows)
                isbns = pd.concat([df.isbn10.dropna(), df.isbn13.dropna()]).unique()
                # 一次輸出一個
                for isbn in isbns:
                    yield isbn
            else:
                no_rows_counter += 1

    @classmethod
    async def bid_Queue_put(cls, t=1):
        '''從博客來的isbn塞進茉莉的Q'''
        await asyncio.sleep(t)
        #
        cls.bid_C = cls.bid_cycle()  # collections.abc.AsyncGenerator
        cls.bid_Q = asyncio.Queue(q_size)
        #
        c = super().bid_Queue_put(cls.bid_C, cls.bid_Q)
        asyncio.create_task(c)

    @classmethod
    async def bid_update_loop(cls, t=2):
        '''茉莉對博客來isbn的無窮爬蟲'''
        await asyncio.sleep(t)
        #
        while 1:
            # (1) 茉莉太快，一次2個就好
            bids = [await cls.bid_Q.get() for _ in range(2)]
            # (2) 由父類篩選書號，跑task
            result = await super().bid_update_loop(bids=bids, DWU=1)
            # (3) 有爬，下次等十秒
            await asyncio.sleep(result * 10)
