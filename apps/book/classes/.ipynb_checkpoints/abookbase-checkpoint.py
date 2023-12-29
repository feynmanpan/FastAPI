from abc import ABC, ABCMeta, abstractmethod
import aiohttp
import asyncio
import re
from collections import namedtuple
import os
import itertools
from typing import Dict, Any, Awaitable, Union
import random
from time import time
from datetime import datetime
import collections
#
import sqlalchemy as sa
import pandas as pd
# from async_property import async_property
#
from apps.sql.config import dbwtb
import apps.ips.config as ipscfg
from apps.ips.config import cacert
from apps.ips.model import IPS
from apps.book.model import INFO
from apps.book.config import (
    dt_format,
    timeout,
    top_proxy_max,
    update_errcnt_max,
    days_without_update,
)
#
##########################################################


class VALIDATE(ABCMeta):
    def __new__(cls, name, bases, class_dict):
        # 不驗證 BOOKBASE
        if (base := bases[0]) != object:
            # 檢查子類info_default的key
            info_cols = base.info_cols
            info_default = class_dict.get('info_default', base.info_default)
            if not isinstance(info_default, dict):
                raise TypeError(f'【{name}】的info_default不是dict')
            if 'bookid' not in info_default:
                raise KeyError(f'【{name}】的info_default中，需有bookid欄位')
            if not isinstance(info_default['bookid'], str):
                raise TypeError(f'【{name}】的info_default的bookid不是str')
            if info_default['bookid'] == "":
                info_default['bookid'] = base.bookid_default
            #
            set0 = set(info_cols)
            set1 = set(info_default.keys())
            if (rest := set1 - set0) != base.empty:
                raise KeyError(f'info_default中，欄位{rest}不在BOOKBASE的info_cols裡面')
            # 造子類的預設info並assign，以子類類名為store名稱
            info_default = base.info_default | info_default
            info_default[base.INFO_COLS.store] = name
            class_dict['info_default'] = info_default
            # 子類管理自己的instance
            class_dict['objs'] = {}
            # 將子類註冊入BOOKBASE
            newcls = super().__new__(cls, name, bases, class_dict)
            base.register_subclasses[name] = newcls
        else:
            newcls = super().__new__(cls, name, bases, class_dict)
        #
        return newcls


class BOOKBASE(object, metaclass=VALIDATE):
    '''所有store的base'''
    register_subclasses = {}  # 註冊所有子類
    #
    info_cols = [
        'store',
        'bookid', 'isbn10', 'isbn13',
        'title', 'title2',
        'author',
        'publisher', 'pub_dt', 'lang',
        'price_list', 'price_sale',
        'stock',
        'spec', 'intro', 'comment',
        'url_book', 'url_vdo', 'url_cover',
        'lock18',
        'err',
        'create_dt',
    ]
    INFO_COLS = namedtuple('INFO_COLS', info_cols)(*info_cols)
    #
    update_default = {INFO_COLS.err: None}
    bookid_default = '__1234567890'
    info_default = {**dict.fromkeys(info_cols, None), **{'bookid': bookid_default}}
    #
    isbn_pattern = '^[0-9]{9}[0-9X]$|^[0-9]{13}$'
    bookid_pattern = ''
    int_pattern = '^[0-9]+$'
    float_pattern = r'^[0-9]*\.*[0-9]*$'
    int_err = 1234567
    float_err = 4567.89
    #
    bid = ''
    update_errcnt = 0
    uids = 0
    objs = {}
    _ss = {}
    now_proxy = ''
    _lock18 = None
    page_err = []
    #
    cwd = os.path.dirname(os.path.realpath(__file__))
    #
    top_proxy = set()
    path_top_proxy = os.path.join(cwd, 'top_proxy.csv')
    if os.path.isfile(path_top_proxy):
        top_proxy = set(pd.read_csv(path_top_proxy).proxy.tolist())
    len_top_proxy = len(top_proxy)
    #
    empty = set()

    # __________________________________________________________
    def __new__(cls, **init):
        '''讓各家store的每個bookid只會有一個instance'''
        bid = init.get('bookid') or cls.info_default['bookid']
        # 沿用或new
        if not (obj := cls.objs.get(bid)):
            obj = object.__new__(cls)
            obj.bid = bid
        #
        return obj

    def __init__(self, **init):
        '''由base處理self.info初始化，並加入class.objs'''
        # 未註冊至class.objs，則初始化
        if not self.objs.get(self.bid):
            self.info = self.info_default | init
            self.info_init = self.info | {}
            # 加入class.objs
            self.objs[self.bid] = self

    def __getattr__(self, name):
        '''self.title = self.info['title']'''
        if name in self.info_cols:
            return self.info[name]
        else:
            raise AttributeError(f'無此屬性:"{name}"')

    # __________________________________________________________

    @property
    def info(self) -> Dict[str, Any]:
        '''主要書籍資訊'''
        return self._info

    @info.setter
    def info(self, val: Dict[str, Any]):
        '''self.info被assign時，用property驗證，驗證失敗也記錄在err'''
        try:
            ######################## 嚴重err ########################
            # (0)檢查assign為dict _________________________________________________________________
            if not isinstance(val, dict):
                raise TypeError('assign給info的值不是dict')
            # (1)檢查欄位 _________________________________________________________________
            set0 = set(self.info_cols)
            set1 = set(val.keys())
            if (rest := set1 - set0) != self.empty:
                raise KeyError(f'assign給info的欄位{rest}不在BOOKBASE的info_cols裡面')
            if (rest := set0 - set1) != self.empty:
                raise KeyError(f'assign給info的欄位缺少:{rest}')
            if set0 != set1:
                raise KeyError(f'assign給info的欄位不等於info_cols')
            ######################## 嚴重err ########################

            # (2)檢查bookid格式 _________________________________________________________________
            bid = val.get(self.INFO_COLS.bookid)
            bid_pn = self.bookid_pattern
            if (bid and bid_pn) and not re.match(bid_pn, bid):
                raise ValueError(f'bookid=【{bid}】 不符合bookid_pattern=【{bid_pn}】')
            # (3)檢查isbn _________________________________________________________________
            isbn_pn = self.isbn_pattern
            isbn10 = val.get(self.INFO_COLS.isbn10)
            isbn13 = val.get(self.INFO_COLS.isbn13)
            if isbn10 and isbn_pn:
                if not re.match(isbn_pn, isbn10):
                    raise ValueError(f'isbn10=【{isbn10}】 不符合isbn_pattern=【{isbn_pn}】')
                if not self.isbn_check(isbn10):
                    raise ValueError(f'isbn10=【{isbn10}】 沒通過isbn_check')
            if isbn13 and isbn_pn:
                if not re.match(isbn_pn, isbn13):
                    raise ValueError(f'isbn13=【{isbn13}】 不符合isbn_pattern=【{isbn_pn}】')
                if not self.isbn_check(isbn13):
                    raise ValueError(f'isbn13=【{isbn13}】 沒通過isbn_check')
            # (4)檢查定價售價 _________________________________________________________________
            if PL := val.get(self.INFO_COLS.price_list):
                if not isinstance(PL, int) or PL < 0:
                    raise ValueError(f'price_list=【{PL}】 需為int，且>=0')
            if PS := val.get(self.INFO_COLS.price_sale):
                if not isinstance(PS, (float, int)) or PS < 0:
                    raise ValueError(f'price_sale=【{PS}】 需為float/int，且>=0')
        #
        except (TypeError, KeyError) as e:
            raise e  # 嚴重err繼續提報
        except Exception as e:
            err1 = val.get('err', '') or ''
            err2 = str(e)
            err = (err2 in err1) and err1 or f"{err2}{'_'*bool(err1)}{err1}"
            val['err'] = err
        ######################################
        self._info = val

    @property
    async def proxy(self) -> Union[str, None]:
        '''從 top_proxy 及 ips_Queue 取proxy'''
        proxy = None
        # (1) 抓top_proxy
        if top_proxy := list(self.top_proxy):
            proxy = random.choice(top_proxy)
        # (2) 抓ips_Queue
        if ippt := await ipscfg.ips_Queue.get():
            tmp = f"http://{ippt['ip']}:{ippt['port']}"
            if proxy:
                # 失敗越多次，提供top_proxy的選取機率
                proxy = random.choice([proxy] + [tmp] * (update_errcnt_max + 3 - self.update_errcnt))
            else:
                proxy = tmp
        # ______________________________________
        return proxy

    @property
    def ss(self) -> aiohttp.ClientSession:
        '''各家用自己家的一個session，存在base，登入過可reuse'''
        store = self.store
        if not self._ss.get(store, None):
            connector = aiohttp.TCPConnector(ssl=cacert, limit=100)
            TO = aiohttp.ClientTimeout(total=timeout)
            self._ss[store] = aiohttp.ClientSession(connector=connector, timeout=TO)
        #
        return self._ss[store]

    @abstractmethod
    async def update_info(self, uid=None, proxy=None, db=dbwtb) -> Union[int, None, bool]:
        '''爬蟲更新self.info，並只留 uid=1 進行爬蟲 '''
        self._stime = time()
        await asyncio.sleep(random.random())
        #
        if uid is None:
            if self.uids == 0:
                uid = self.uids = 1
            else:
                # 若有 uid=1 在跑了，等到前一個跑完才離開，確保得到一樣的info
                print('等待uids=1...')
                while self.uids == 1:
                    await asyncio.sleep(0.5)
                print('等待uids=1>0...over')
        # 要爬蟲時，對所需變數進行初始化
        if uid == 1:
            self.now_proxy = proxy or await self.proxy
            self._enter_bookpage = False
            self._login_success = False
            self._update: Dict[str, Any] = self.update_default | {}
        #
        return uid

    async def update_final(self, uid, db=dbwtb) -> Union[int, None, bool]:
        '''每次爬蟲結束，finally進行判斷: 停止/繼續'''
        if (not self._enter_bookpage) and (self._lock18 and self._login_success):
            self.update_errcnt = 0
            print('登入成功，重get 18禁單書頁')
            #
            self._update_result = await self.update_info(proxy=self.now_proxy, uid=uid, db=db)
        else:
            success = not self._update['err'] or self._update['err'] in self.page_err
            limit = self.update_errcnt == update_errcnt_max
            # 成功或耗盡次數都stop，抓成功/頁面連接錯誤，可以存db
            if success or limit:
                if success:
                    self._update['create_dt'] = datetime.today().strftime(dt_format)
                    self.info = self.info_init | self._update
                    await self.save_info(db=db)  # 資料都通過info setter的檢查才存db
                #
                self._update_result = success
                self.update_errcnt = 0
                self.uids = 0
                #
                print(f"{self.now_proxy:<30}, duration = {time()-self._stime}{success*', 【儲存DB】'}{(not success)*', 【爬蟲次數用盡】'}\n")
            else:
                self.update_errcnt += 1
                print(f"{self.now_proxy:<30}, errcnt={self.update_errcnt}/{update_errcnt_max}_uid={uid}, err={self._update['err']}\n")
                #
                self._update_result = await self.update_info(uid=uid, db=db)
        #
        return self._update_result

    async def read_or_update(self, db=dbwtb, fd: int = 0):
        '''讀取cls.objs > db > 重新爬蟲'''
        if fd:
            print('強制重新爬蟲')
            result = await self.update_info(db=db)
            print(f'強制重新爬蟲結果:{result}')
        elif self.create_dt:
            print('沿用cls.objs裡面')
        elif result := await self.read_info(db=db):
            print(f'從db抓結果:{result}')
        else:
            print('重新爬蟲')
            result = await self.update_info(db=db)
            print(f'重新爬蟲結果:{result}')

    async def read_info(self, db=dbwtb) -> bool:
        '''select * from dbwtb.info'''
        cs = INFO.__table__.columns
        w1 = INFO.store == self.store
        w2 = INFO.bookid == self.bid
        #
        query = sa.select(cs).where(w1).where(w2)
        rows = await db.fetch_all(query)
        #
        info = rows and dict(rows[0]) or {}
        info.pop('idx', None)
        #
        if info:
            self.info = info
        #
        return bool(info)

    async def save_info(self, db=dbwtb):
        '''self.info >> dbwtb.info'''
        cs = [
            INFO.idx,
        ]
        w1 = INFO.store == self.store
        w2 = INFO.bookid == self.bid
        #
        query = sa.select(cs).where(w1).where(w2)
        rows = await db.fetch_all(query)
        # 決定更新或插入
        if rows:
            idx = rows[0]['idx']
            UI_query = sa.update(INFO).values(**self.info).where(INFO.idx == idx)
        else:
            UI_query = sa.insert(INFO).values(**self.info)
        #
        await db.execute(UI_query)

    @classmethod
    async def close_ss(cls):
        '''關閉base._ss的所有session'''
        for ss in cls._ss.values():
            await ss.close()
        cls._ss = {}
        print('關閉base._ss的所有session')

    @classmethod
    def top_proxy_tocsv(cls):
        '''app shutdown時儲存top_proxy'''
        if cls.top_proxy and ((len_top_proxy := len(cls.top_proxy)) > cls.len_top_proxy):
            print(f'top_proxy增加為{len_top_proxy}，上限{top_proxy_max}個，儲存csv')
            tmp = list(cls.top_proxy)
            random.shuffle(tmp)
            pd.DataFrame({'proxy': tmp[:top_proxy_max + 1]}).to_csv(cls.path_top_proxy, index=False)
        else:
            print(f'top_proxy數量不變={cls.len_top_proxy}')
            
    def price_sub(self, price: str) -> str:
        '''只保留0-9及小數點'''
        return re.sub('[^.0-9]', '', price)

    def price_list_handle(self, price_list) -> Union[int, None]:
        '''定價售價統一base處理'''
        if price_list:
            price_list  = self.price_sub(price_list)
            price_list = not re.match(self.int_pattern, price_list) and self.int_err or int(price_list)
        return price_list

    def price_sale_handle(self, price_sale) -> Union[int, float, None]:
        '''定價售價統一base處理'''
        if price_sale:
            price_sale  = self.price_sub(price_sale)
            if not re.match(self.float_pattern, price_sale):
                price_sale = self.float_err
            else:
                price_sale = float(price_sale)
                if price_sale == (tmp := int(price_sale)):
                    price_sale = tmp
        return price_sale

    def update_handle(self, locals_var):
        '''爬成功的update統一base處理'''
        for col in self.info_cols:
            if (val := locals_var.get(col)) not in ['', None]:
                self._update[col] = val

    def page_err_handle(self, rtext: str, status):
        '''有回應，但不是要爬的單書頁時之處理'''
        for pe in self.page_err:
            if pe in rtext:
                self._update['err'] = pe
                break
        else:
            self._update['err'] = f'status={status},rtext={rtext[:100]}'

    ##################  連續書號查詢 ##################

    @staticmethod
    def isbn_generator(body: str) -> str:
        '''
        body為前9位或12位數，根據檢查規則產出末位檢查碼
        https://zerojudge.tw/ShowProblem?problemid=b536
        '''
        #
        body = body and body.replace('-', '').strip()
        if not body or not re.match('^[0-9]{9}$|^[0-9]{12}$', body):
            return '123456789X'
        #
        body_L = [int(i) for i in list(body)]
        if len(body) == 9:
            # 9位分別乘以10 9 8 7 6 5 4 3 2
            S = sum(n * i for n, i in zip(range(10, 1, -1), body_L))
            N = 11 - S % 11
            X = (N == 10) * 'X' or (N == 11) * '0' or N
        else:
            # 12位分別乘以1,3,1,3,1,3,1,3,1,3,1,3
            S = sum(n * i for n, i in zip([1, 3] * 6, body_L))
            N = 10 - S % 10
            X = (N == 10) * '0' or N
        #
        return f'{body}{X}'

    @classmethod
    def isbn_check(cls, isbn: str) -> bool:
        '''根據 isbn_generator 檢查ISBN格式'''
        #
        isbn = isbn and isbn.replace('-', '').strip().upper()
        if not isbn or not re.match(cls.isbn_pattern, isbn):
            return False
        #
        return isbn == cls.isbn_generator(isbn[:-1])

    @classmethod
    async def bid_Queue_put(cls, C, Q: asyncio.Queue):
        '''base對書號queue無窮put'''
        while 1:
            if isinstance(C, collections.abc.AsyncGenerator):
                bid = await C.__anext__()
            else:
                bid = next(C)
            #
            await Q.put(bid)
            print(f'{cls.__name__:<10}:bid_Queue_put {bid}')

    @classmethod
    async def bid_update_loop(cls, bids: list, DWU: int = days_without_update) -> bool:
        '''DB有已經爬過的書號時，進行篩選，有些不重爬'''
        cs = [INFO.bookid, INFO.err, INFO.create_dt]
        w1 = INFO.store == cls.__name__
        w2 = INFO.bookid.in_(bids)
        #
        query = sa.select(cs).where(w1 & w2)
        rows = await dbwtb.fetch_all(query)
        # (1) DB有書號，進行篩選
        if rows:
            skip = set()
            today = datetime.today()
            for r in rows:
                create_dt = datetime.strptime(r['create_dt'], dt_format)
                D = (today - create_dt).days
                if D <= DWU or r['err'] in cls.page_err:
                    skip.add(r['bookid'])
            #
            bids = set(bids) - skip
        # (2) 篩選後有剩，進行重爬
        if bids:
            tasks = []
            for bid in bids:
                book = cls(bookid=bid)
                c = book.update_info()
                tasks.append(asyncio.create_task(c))
            #
            await asyncio.wait(tasks)
        #
        return bool(bids)
