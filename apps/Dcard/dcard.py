from typing import Union
import aiohttp
import pandas as pd
import os


#################################


class Dcard:
    '''
    參考 https://blog.jiatool.com/posts/dcard_api_v2/

    worker = Dcard()
    for pid in pids:
        result = worker.get_posts(before=pid or after='236978250')

    '''
    # _________________________________________________________________________________
    url_index = 'https://www.dcard.tw/'
    url_api = f"{url_index}service/api/v2/posts?popular=false&limit=100"
    #
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    }
    cacert = True
    timeout = 20
    connector = aiohttp.TCPConnector(ssl=cacert, limit=100)
    TO = aiohttp.ClientTimeout(total=timeout)
    ss = aiohttp.ClientSession(connector=connector, timeout=TO)
    #
    csv_name = 'dcard.csv'
    log_name = 'dcard_err.log'
    # _________________________________________________________________________________

    def save_result(self, result, err=False):
        '''儲存爬蟲結果或錯誤log'''
        if not err:
            if os.path.isfile(self.csv_name):
                df1 = pd.read_csv(self.csv_name)
            else:
                df1 = pd.DataFrame()
            #
            df2 = pd.DataFrame(result)
            pd.concat([df1, df2]).drop_duplicates(subset=['id']).sort_values(by=['id'], ascending=False).to_csv(self.csv_name, index=False)
        else:
            with open(self.log_name, 'a') as f:
                f.write(result + '\n')

    async def get_posts(self, url='', before='', after='', proxy=None) -> Union[list, str]:
        '''
            取得最新100篇文章
        '''
        result: Union[list, str] = ''
        if not url:
            url = self.url_api + f'&before={before}' * bool(before) + f'&after={after}' * bool(after)
        # _______________________________________________
        try:
            async with self.ss.get(self.url_index, headers=self.headers, proxy=proxy) as r:
                if r.status == 200:
                    async with self.ss.get(url, headers=self.headers, proxy=proxy) as r:
                        if r.status == 200:
                            result = await r.json(encoding='utf8')
                        else:
                            result = await r.text(encoding='utf8')
        except Exception as e:
            self.save_result(repr(e), err=True)
        else:
            try:
                self.save_result(result, err=not isinstance(result, list))
            except Exception as e:
                self.save_result(e, err=True)
        finally:
            return result
