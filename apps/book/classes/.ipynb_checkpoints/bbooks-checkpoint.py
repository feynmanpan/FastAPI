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
from typing import Dict, Any, Callable, Awaitable, Coroutine, Optional, Tuple, Union
from PIL import Image
from pyquery.pyquery import PyQuery
import pytesseract
import copy
import itertools
import sqlalchemy as sa
from sqlalchemy import desc
from sqlalchemy.sql import func
#
from apps.sql.config import dbwtb
from apps.book.model import INFO
from apps.book.classes.abookbase import BOOKBASE
import apps.ips.config as ipscfg
from apps.ips.config import ips_csv_path, dtype, cacert, headers
from apps.book.config import (
    dt_format,
    login,
    q_size,
    days_without_update,
)
###################################################


class BOOKS(BOOKBASE):
    '''博客來'''
    store_name = '博客來'
    info_default = {
        "bookid": "0010770978",  # 刺殺騎士團長
    }
    #
    bid_prefixes = ['00', 'CN', 'F0']  # 中文_簡體_外文
    bid_digits = 8
    bookid_pattern = '^00[0-9]{8}$|^CN[0-9]{8}$|^F0[0-9]{8}$'
    comment_js_pattern = '<script type="text/javascript">(.|\n)+?</script>'
    # 首頁
    url_home = 'https://www.books.com.tw'
    # 單書頁
    url_prod_prefix = f"{url_home}/products/"
    # 評論及庫存都要ajax
    url_prodshow = f'{url_home}/product_show/'
    tail = ':A:M201101_0_getCommentData_P00a400020068:getCommentAjax:M201101_078_view/M201101_078_view'
    url_comment_ajax = url_prodshow + 'getCommentAjax/{}:{}' + tail
    url_cart_ajax = url_prodshow + 'getProdCartInfoAjax/{}/M201105_032_view'
    # 登入頁
    url_cart_dns = 'https://cart.books.com.tw'
    url_login = f'{url_cart_dns}/member/login'
    url_loginpost = f'{url_cart_dns}/member/login_do/'
    #
    bookpage_str = '商品介紹'
    lock18_str = '限制級商品'
    page_err = [
        '頁面連結錯誤',
        'disallowed characters',
        # 'The Event ID',
        # '限制級商品'
    ]
    # 登入18禁用的帳密
    account = login['BOOKS'][0]
    passwd = login['BOOKS'][1]
    #
    start_L = [0, 10**7]
    start_L_new = start_L[:]
    # __________________________________________________________

    def __init__(self, **init):
        super().__init__(**init)
        self.url_prod = f"{self.url_prod_prefix}{self.bid}"
        self.headers_Referer = headers | {'Referer': self.url_prod}
        self.headers_Referer_login = headers | {'Referer': f'{self.url_login}?url={self.url_prod}'}
    # __________________________________________________________

    async def update_info(self, proxy: Optional[str] = None, uid: Optional[int] = None, db=dbwtb):
        # ======== 只留 uid=1 進行爬蟲，其他則等待及結束 =======
        if (uid := await super().update_info(uid=uid, proxy=proxy)) != 1:
            return self._update_result
        # ===================================================
        try:
            # 抓單書頁資訊
            print(f'{self.bid}__get 單書頁---------------------')
            async with self.ss.get(self.url_prod, headers=headers, proxy=self.now_proxy) as r:
                status = r.status
                rtext = await r.text(encoding='utf8')
            #
            if (status == 200) and (self.bid in rtext):
                # 成功的代理存到bookbase
                self.top_proxy.add(self.now_proxy)
                # 判斷商品，登入過18禁的session下次就不會再登入
                self._enter_bookpage = self.bookpage_str in rtext
                if self._lock18 is None:
                    self._lock18 = self.lock18_str in rtext  # 未登入/單書頁都有限制級商品字串
                #
                print(f'進入單書頁={self._enter_bookpage}, 限制級商品={self._lock18}')
        except asyncio.exceptions.TimeoutError as e:
            self._update['err'] = 'asyncio.exceptions.TimeoutError'
        except Exception as e:
            self._update['err'] = str(e)
        else:
            if self._enter_bookpage:
                # 確定進入單書頁
                print('bookpage_handle ---------------------')
                try:
                    result = await self.bookpage_handle(rtext)
                    self.update_handle(result)
                except asyncio.exceptions.TimeoutError as e:
                    self._update['err'] = 'enter_bookpage_asyncio.exceptions.TimeoutError'
                except Exception as e:
                    self._update['err'] = str(e)
            elif self._lock18:
                # 18禁，直到登入成功
                print('嘗試登入---------------------')
                try:
                    while not self._login_success:
                        capcha = await self.get_capcha()
                        if capcha:
                            self._login_success = await self.loginpost(capcha)
                            if self._login_success:
                                print('成功capcha=', capcha)
                            else:
                                print('登入失敗')
                except asyncio.exceptions.TimeoutError as e:
                    self._update['err'] = 'lock18_asyncio.exceptions.TimeoutError'
                except Exception as e:
                    self._update['err'] = str(e)
            else:
                self.page_err_handle(rtext, status)
        finally:
            return await self.update_final(uid=uid, db=db)

    async def bookpage_handle(self, rtext) -> Dict[str, Any]:
        '''單書頁處理，回傳locals()'''
        lock18 = self._lock18
        # (1) ajax 抓庫存及評論 =========================================================================
        stock = await self.stock_handle()
        comment = await self.comment_handle()
        # (2) 單書頁 =========================================================================
        doc = pq(rtext, parser='html')
        #
        isbn = doc.find(".mod_b.type02_m058.clearfix .bd ul li:Contains('ISBN')").eq(0).text().__str__().replace("ISBN：", "").strip()
        if (len_isbn := len(isbn)) >= 10:
            isbn10 = (len_isbn == 10 and isbn) or None
            isbn13 = (len_isbn == 13 and isbn) or None
        # _________________________________________________________________________
        title = doc.find('.mod.type02_p002.clearfix > h1').eq(0).text().__str__().strip()
        title2 = doc.find(".mod.type02_p002.clearfix > h2").eq(0).text().__str__().strip()
        # _________________________________________________________________________
        el = doc.find(".type02_p003.clearfix ul").eq(0)
        author = self.author_handle(el)
        publisher = self.publisher_handle(el)
        pub_dt = self.pub_dt_handle(el)
        lang = el.find("li:Contains('語言')").eq(0).text().__str__().replace('語言：', '').strip()
        # _________________________________________________________________________
        el = doc.find(".prod_cont_a ul.price").eq(0)
        price_list, price_sale = self.price_handle(el)
        spec = doc.find(".mod_b.type02_m058.clearfix .bd li:Contains('規格')").eq(0).text().__str__().replace(" ", "").replace("規格：", "").strip()
        intro = doc.find(".bd .content").eq(0).html()
        # _________________________________________________________________________
        url_book = self.url_prod
        url_vdo = doc.find('.cont iframe').eq(0).attr('src')  # 沒影片時為None
        url_cover = doc.find(".cover_img > img.cover").attr("src")
        #
        return locals()

    def author_handle(self, el: PyQuery):
        authors = el.find("li").find("a[href*='adv_author']")
        author = ''
        for au in authors:
            parenttext = pq(au).parent().text().__str__().strip()
            name = pq(au).text().__str__().strip()
            #
            if '作者' in parenttext and '原文作者' not in parenttext:
                author += f'作者：{name}/'
            elif '原文作者' in parenttext:
                author += f'原文作者：{name}/'
            elif '譯者' in parenttext:
                author += f'譯者：{name}/'
            elif '編者' in parenttext:
                author += f'編者：{name}/'
        #
        author = author.strip('/')
        return author

    def publisher_handle(self, el: PyQuery):
        publisher = el.find("a[href*='sys_puballb']").eq(0).text().__str__().strip()
        # --原文出版社
        if not publisher:
            publisher = el.find("li:Contains('原文出版社')").eq(0).text().__str__().replace('原文出版社：', '').strip()
        return publisher

    def pub_dt_handle(self, el: PyQuery):
        pub_dt = el.find("li:Contains('出版日期')").eq(0).text().__str__().replace('出版日期：', '').replace('/', '-').strip()
        # pub_dt = datetime.strptime(pub_dt, pub_dt_format).date()
        return pub_dt

    def price_handle(self, el: PyQuery) -> Tuple[Union[str, int], Union[str, float, int]]:
        price_list = el.find("em").eq(0).text().__str__().strip()
        price_sale = el.find("strong.price01").eq(-1).find("b").eq(0).text().__str__().strip()  # 有優惠價跟特價，要找最後一個
        if price_sale and not price_list:
            price_list, price_sale = price_sale, price_list  # F010000010 的情形
        # 定價售價統一base處理
        price_list = self.price_list_handle(price_list)
        price_sale = self.price_sale_handle(price_sale)
        #
        return price_list, price_sale

    async def stock_handle(self) -> Union[str, None]:
        '''抓ajax庫存'''
        await asyncio.sleep(0.05)
        url_cart_ajax = self.url_cart_ajax.format(self.bid)
        #
        async with self.ss.get(url_cart_ajax, headers=self.headers_Referer, proxy=self.now_proxy) as r2:
            status2 = r2.status
            rtext2 = await r2.text(encoding='utf8')
            if (status2 == 200) and rtext2:
                return pq(rtext2, parser='html').find("div.mc002.type02_p008 ul.list li.no").eq(0).text().__str__().strip()

    async def comment_handle(self) -> Union[str, None]:
        '''抓ajax評論'''
        await asyncio.sleep(0.15)
        url_comment_ajax = self.url_comment_ajax.format(self.bid, 1)
        # 先看第一頁評論結果
        async with self.ss.get(url_comment_ajax, headers=self.headers_Referer, proxy=self.now_proxy) as r2:
            status2 = r2.status
            rtext2 = await r2.text(encoding='utf8')
            # 看一共幾頁
            if (status2 == 200) and rtext2:
                pn = pq(rtext2, parser='html').find(".cnt_page > .page > span").eq(0).text().__str__().strip()
                pn = bool(pn) and int(pn) or 0
                if pn:
                    for p in range(2, pn + 1):
                        await asyncio.sleep(0.15)
                        url_comment_ajax = self.url_comment_ajax.format(self.bid, p)
                        async with self.ss.get(url_comment_ajax, headers=self.headers_Referer, proxy=self.now_proxy) as r:
                            rtext = await r.text(encoding='utf8')
                            rtext2 += rtext
                # 去除js
                return re.sub(self.comment_js_pattern, '', rtext2)

    async def loginpost(self, capcha) -> Union[bool, None]:
        '''遞交登入'''
        formdata = {
            'captcha': capcha,
            'login_id': self.account,
            'login_pswd': self.passwd,
        }
        #
        async with self.ss.post(self.url_loginpost, headers=self.headers_Referer_login, proxy=self.now_proxy, data=formdata) as r:
            if r.status == 200:
                rtext = await r.text(encoding='utf8')
                result = json.loads(rtext)
                success = result['success']
                if not success and '六個月' in (tmp := str(result)):
                    # 太久沒修改密碼，持續提醒
                    while 1:
                        print((tmp + '\n') * 10)
                        await asyncio.sleep(2)
                return success

    async def get_capcha(self) -> Union[str, None]:
        '''從登入頁面抓capcha圖檔及OCR'''
        capcha = None
        async with self.ss.get(self.url_login, headers=headers, proxy=self.now_proxy) as r:
            if r.status == 200:
                rtext = await r.text(encoding='utf8')
                doc = pq(rtext, parser='html')
                url_capcha = self.url_cart_dns + doc.find("#captcha_img img").attr('src').__str__()
                # OCR
                async with self.ss.get(url_capcha, headers=headers, proxy=self.now_proxy) as r:
                    if r.status == 200:
                        jpg = os.path.join(self.cwd, url_capcha.split('?')[-1] + '.jpg')
                        print(f'儲存capcha: {jpg}')
                        f = await aiofiles.open(jpg, mode='wb')
                        await f.write(await r.read())
                        await f.close()
                        #
                        try:
                            if os.path.getsize(jpg) == 0:
                                raise ValueError('jpg 0 KB')
                            img = Image.open(jpg)
                            img = self.convert_img(img)
                            capcha = pytesseract.image_to_string(img).__str__().strip()
                        except Exception as e:
                            os.remove(jpg)
                            print(repr(e))
                        else:
                            os.rename(jpg, os.path.join(self.cwd, 'last_capcha.jpg'))
        #
        return capcha

    def convert_img(self, img):
        '''登入的驗證碼圖片轉成黑白'''
        pixels = img.load()
        R, G, B = [87, 98, 201]
        for x in range(img.width):
            for y in range(img.height):
                r, g, b = pixels[x, y]
                delta = abs(R - r) + abs(G - g) + abs(B - b)
                if delta < 30:
                    pixels[x, y] = (0, 0, 0)
                else:
                    pixels[x, y] = (255, 255, 255)
        return img

    ##################  連續書號查詢 ##################

    @classmethod
    def bid_cycle(cls, prefix: str = '00', digits: int = 8, start: int = 0):
        '''製造書號'''
        # bookid_pattern = '^00[0-9]{8}$|^CN[0-9]{8}$|^F0[0-9]{8}$'  # 中文_簡體_外文
        # 從 0 到 99999999 不斷循環
        # (1) 檢查prefix
        bid_pattern = cls.bookid_pattern
        bid_prefixes = cls.bid_prefixes  # [p[1:3] for p in bid_pattern.split('|')]
        if prefix not in bid_prefixes:
            raise ValueError(f'書號prefix: {prefix} 不對，須為{bid_prefixes}之一')
        # (2) 循環輸出流水書號
        for i in itertools.cycle(range(start, 10**digits)):
            bid = f'{prefix}{i:0{digits}}'
            if not re.match(bid_pattern, bid):
                raise ValueError(f'{bid} 不符合bookid_pattern="{bid_pattern}"')
            yield bid

    @classmethod
    async def bid_Queue_put(cls, t=0):
        '''創造博客來三種書號的無窮put'''
        await asyncio.sleep(t)
        #
        prefixes = cls.bid_prefixes
        digits = cls.bid_digits
        # (1) 查詢DB最大書號，更新 start_L
        # cs = [INFO.bookid]
        cs = [sa.func.max(INFO.bookid)]
        w1 = INFO.store == cls.__name__
        # w2 = INFO.bookid == func.max(INFO.bookid).select()
        query = sa.select(cs).where(w1)  # .order_by(desc(INFO.bookid)).limit(1)
        rows = await dbwtb.fetch_all(query)
        if rows:
            max_bid = int(rows[0]['max_1'][2:])
            if cls.start_L[1] * 10 - 1 > max_bid > cls.start_L[1]:
                cls.start_L_new = [max_bid - cls.start_L[1], max_bid]
        # (2) 根據前綴及start_L，造對應數量的cycle, queue
        cls.bid_Cs = [cls.bid_cycle(prefix=p, digits=digits, start=s) for s in cls.start_L_new for p in prefixes]
        cls.bid_Qs = [asyncio.Queue(q_size) for _ in cls.start_L_new for __ in prefixes]
        # 每組CQ各自task
        for C, Q in zip(cls.bid_Cs, cls.bid_Qs):
            c = super().bid_Queue_put(C, Q)
            asyncio.create_task(c)

    @classmethod
    async def bid_update_loop(cls, t=1):
        '''對博客來三種書號的無窮爬蟲'''
        await asyncio.sleep(t)
        #
        while 1:
            # (1) 6個書號一組，3種書號每種各2個，一個0開始，一個10000000
            bids = [await Q.get() for Q in cls.bid_Qs]
            # (2) 由父類篩選書號，跑task
            await super().bid_update_loop(bids=bids)
