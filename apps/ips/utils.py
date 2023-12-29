import asyncio
import aiohttp
import re
import random
import pandas as pd
#
from .config import (
    cacert, headers, ipcols, ipcols_err, maxN,
    proxy_checkurls, timeout, check_atleast, sampleN,
    ips_err_csv_path,
)

########################################################


def write_file(fpath, text):
    with open(fpath, 'w') as f:
        f.write(text)


async def aio_get(session, url: str):
    async with session.get(url, headers=headers) as r:
        status_code = r.status
        # print(f'status_code={status_code}')
        if status_code == 200:
            rep = await r.text(encoding='utf8')
        else:
            rep = None
        return status_code, rep


def csv_update(df1, df2):
    # 保留500筆
    return df1.append(df2).sort_values(by=ipcols, ascending=True).drop_duplicates(subset=ipcols[:2]).reset_index(drop=True)[:maxN]


class CHECK_PROXY:
    ips_err = []

    def __init__(self, ip, port, now=''):
        self.ip = ip
        self.port = port
        self.now = now
        self.proxy = f"http://{ip}:{port}"  # aiohttp只支援http的proxy
        self._isGood = []

    async def check(self, proxy_checkurl):
        connector = aiohttp.TCPConnector(ssl=cacert)
        TO = aiohttp.ClientTimeout(total=timeout)
        TF = False
        try:
            await asyncio.sleep(random.randint(0, sampleN - 1))
            async with aiohttp.ClientSession(connector=connector, timeout=TO) as session:
                async with session.get(proxy_checkurl, headers=headers, proxy=self.proxy) as r:
                    status = r.status
                    rtext = await r.text()
                    # rtext = await r.text(encoding='utf8')
        except asyncio.exceptions.TimeoutError as e:
            self.ips_err_append('asyncio.exceptions.TimeoutError', proxy_checkurl)
        except Exception as e:
            self.ips_err_append(str(e), proxy_checkurl)
        else:
            TF = (status == 200) and re.search(self.ip, rtext) is not None
            if not TF:
                self.ips_err_append(f'status={status}, or ip not show in checkurl', proxy_checkurl)
        finally:
            self._isGood.append(TF)

    async def isGood(self):
        tasks = [asyncio.create_task(self.check(url)) for url in random.sample(proxy_checkurls, sampleN)]
        await asyncio.wait(tasks)
        p = None
        if (goodcnt := sum(self._isGood)) >= check_atleast:
            p = {
                'ip': self.ip,
                'port': self.port,
                'now': self.now,
                'goodcnt': goodcnt,
            }
        return p

    def ips_err_append(self, err, checkurl):
        p = {
            'ip': self.ip,
            'port': self.port,
            'err': err,
            'checkurl': checkurl,
        }
        self.ips_err.append(p)  # 存到cls.ips_err

    @classmethod
    async def get_good_proxys(cls, ippts: list):
        # 檢查每個proxy，挑出至少成功一次者
        tasks = [asyncio.create_task(cls(*ippt).isGood()) for ippt in ippts]
        good_proxys = [p for p in await asyncio.gather(*tasks) if p]
        # 儲存完全失敗者
        gip = [p['ip'] for p in good_proxys]
        df = pd.DataFrame(cls.ips_err)
        df = df[~df.ip.isin(gip)].sort_values(by=ipcols_err)  # 至少成功一次者的失敗紀錄略過
        df['g_idx'] = df.groupby(by=['ip']).ngroup()
        df.to_csv(ips_err_csv_path, index=False)
        cls.ips_err = []
        #
        return good_proxys
