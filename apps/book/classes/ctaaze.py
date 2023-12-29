import asyncio
from typing import Any, Dict, Optional, Tuple, Union
from pyquery import PyQuery as pq
from pyquery.pyquery import PyQuery
#
from apps.sql.config import dbwtb
from apps.ips.config import ips_csv_path, dtype, cacert, headers
from apps.book.classes.abookbase import BOOKBASE


###################################################


class TAAZE(BOOKBASE):
    '''讀冊'''
    info_default = {
        "bookid": "11100831442",  # 刺殺騎士團長，11位 https://www.taaze.tw/products/11100831442.html
    }
    #
    bid_digits = 11
    bookid_pattern = f'^11[123][0-9]{{{bid_digits-3}}}$'  # 只抓繁體新,二手書
    # 首頁
    url_home = 'https://www.taaze.tw'
    # 單書頁
    url_prod_prefix = f'{url_home}/products/'

    def __init__(self, **init):
        super().__init__(**init)
        self.url_prod = f"{self.url_prod_prefix}{self.bid}.html"

    async def update_info(
        self,
        proxy: Optional[str] = None,
        uid: Optional[int] = None,
        db=dbwtb,
        proxy_none=False,
    ):
        # ======== 只留 uid=1 進行爬蟲，其他則等待及結束 =======
        if (uid := await super().update_info(uid=uid, proxy=proxy, proxy_none=proxy_none)) != 1:
            return self._update_result
        # ===================================================
        try:
            # 抓單書頁資訊
            print(f'TAAZE {self.bid}__get 單書頁---------------------')
            async with self.ss.get(self.url_prod, headers=headers, proxy=self.now_proxy) as r:
                status = r.status
                rtext = await r.text(encoding='utf8')
            #
            if (status == 200) and (self.url_prod in rtext):
                # 成功的代理存到bookbase
                if self.now_proxy:
                    self.top_proxy.add(self.now_proxy)
                #
        except asyncio.exceptions.TimeoutError as e:
            self._update['err'] = 'asyncio.exceptions.TimeoutError'
        except Exception as e:
            self._update['err'] = str(e)
        else:
            result = await self.bookpage_handle(rtext)
            return result
        finally:
            self.uids = 0

    async def bookpage_handle(self, rtext: str) -> Dict[str, Any]:
        '''單書頁處理，回傳locals()'''
        doc = pq(rtext, parser='html')
        # _________________________________________________________________________
        isbn = doc.find("meta[property='books:isbn']").eq(0).attr('content')
        if (len_isbn := len(isbn)) >= 10:
            isbn10, isbn13 = self.isbn1013(isbn, len_isbn)
        # _________________________________________________________________________
        authorBrand = doc.find('div.authorBrand').eq(0)
        title = authorBrand.prev().find("h1").eq(0).text().__str__().strip()
        author = authorBrand.find('a').eq(0).text().__str__().strip()
        publisher = doc.find('span.prodInfo_boldSpan:Contains("出版社") a').eq(0).text().__str__().strip()
        pub_dt = doc.find('span.prodInfo_boldSpan:Contains("出版日期") span').eq(0).text().__str__().strip()
        lang = doc.find('span.prodInfo_boldSpan:Contains("語言：") span').eq(0).text().__str__().strip()
        # _________________________________________________________________________
        divprice = doc.find('div.price').eq(0)
        price_list, price_sale = self.price_handle(divprice)
        #
        return locals()

    def price_handle(self, el: PyQuery) -> Tuple[Union[str, int], Union[str, float, int]]:
        '''新書是優惠價，二手書是二手價'''
        price_list = el.find('span:Contains("定價：") span:last').eq(0).text().__str__().strip()
        price_sale = el.find('span:Contains("優惠價：") span:last').eq(0).text().__str__().strip()
        if not price_sale:
            price_sale = el.find('span:Contains("二手價：") span:last').eq(0).text().__str__().strip()
        # 定價售價統一base處理
        price_list = self.price_list_handle(price_list)
        price_sale = self.price_sale_handle(price_sale)
        #
        return price_list, price_sale
