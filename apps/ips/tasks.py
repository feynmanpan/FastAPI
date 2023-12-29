# -*- coding: utf-8 -*-
import asyncio
# import requests
import aiohttp
from pyquery import PyQuery as pq
import pandas as pd
import os
# import sys
from datetime import datetime
import itertools
import random
from time import time
import sqlalchemy as sa
#
from fastapi import Request
# 為了在jupyter中試，從apps開始import
import apps.ips.config as ips_cfg
from apps.ips.config import (
    url_free_cycle, level_https, cacert,
    ips_csv_path, ips_html_path,
    dtype, dt_format,
    ipcols, get_freeproxy_delta,
)
from apps.ips.utils import aio_get, write_file, csv_update, CHECK_PROXY
from .crud import bulk_insert
#
from .model import IPS  # ,tb_ips
from apps.sql.config import dbwtb
###############################################################################


async def ips_Queue_put(t):
    '''''從 ips_cycle 抓一個到 ips_Queue'''
    await asyncio.sleep(t)
    # (1) 先讀csv ____________________________________________________________________________
    if not ips_cfg.ips_cycle:
        if os.path.isfile(ips_cfg.ips_csv_path):
            rows = pd.read_csv(ips_cfg.ips_csv_path, usecols=['ip', 'port']).to_dict('records')
            if rows:
                ips_cfg.ips_cycle = itertools.cycle(rows)
    # (2) 再讀DB ____________________________________________________________________________
    if not ips_cfg.ips_cycle:
        cs = [
            IPS.ip,
            IPS.port,
        ]
        query = sa.select(cs)  # .order_by('idx').where(tb_ips.columns.id > 100)
        records = await dbwtb.fetch_all(query)
        if records:
            ips_cfg.ips_cycle = itertools.cycle([dict(r) for r in records])
    # (3) 都沒有就給None ____________________________________________________________________________
    if not ips_cfg.ips_cycle:
        ips_cfg.ips_cycle = itertools.cycle([None])
    # (4) 阻塞 put ____________________________________________________________________________
    while 1:
        try:
            ippt = next(ips_cfg.ips_cycle)
            await ips_cfg.ips_Queue.put(ippt)
            print(f'\nips_Queue_put {ippt}\n')
        except:
            await asyncio.sleep(1)


async def get_freeproxy(t, once=True):
    '''代理proxy篩選'''
    get_freeproxy_cnt = 0
    while 1:
        T = 1 + (ips_cfg.ips_cycle and os.path.isfile(ips_csv_path)) * t  # 沒有 csv 或 ips_cycle 就馬上爬
        await asyncio.sleep(T)
        stime = time()
        url_free = next(url_free_cycle)
        #
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=cacert)) as session:
                status_code, rtext = await aio_get(session, url_free)
                if status_code == 200 and rtext not in ['', None]:
                    doc = pq(rtext, parser='html')
                    trs = doc.find('table.table').eq(0).find('tr')
                    if trs.size():
                        now = datetime.today().strftime(dt_format)
                        elite = []
                        for tr in trs:
                            tds = pq(tr).find('td')
                            level = tds.eq(4).text().strip()
                            https = tds.eq(6).text().strip()
                            # _________________________________
                            if (level, https) not in level_https:
                                continue
                            # _________________________________
                            tmp = {
                                'ip': tds.eq(0).text().strip(),
                                'port': tds.eq(1).text().strip(),
                                'now': now,
                                'goodcnt': 0,
                            }
                            elite.append(tmp)
                        if not elite:
                            continue
                        # 1 儲存每次撈取的原始頁面 #################################
                        write_file(ips_html_path, rtext)
                        # 2 重存csv: 讀取csv檔案，與最新爬的比較 #################################
                        if os.path.isfile(ips_csv_path):
                            df1 = pd.read_csv(ips_csv_path, dtype=dtype)
                            df2 = pd.DataFrame(elite).astype(dtype)
                            df3 = csv_update(df1, df2)
                        else:
                            df3 = pd.DataFrame(elite).astype(dtype)
                        # 3 檢查代理 #################################
                        ippts = df3[ipcols].values.tolist()  # goodcnt不傳進CHECK_PROXY
                        print(f'\n開始檢查proxy:共 {len(ippts)} 個 ({url_free})')
                        good_proxys = await CHECK_PROXY.get_good_proxys(ippts)
                        print(f'結束檢查proxy: {time()-stime}')
                        random.shuffle(good_proxys)
                        # 4 存 csv #################################
                        pd.DataFrame(good_proxys).astype(dtype).to_csv(ips_csv_path, index=False)  # df.sample(frac=1)  # 亂排
                        # 5 存 db #################################
                        await bulk_insert(dbwtb, IPS, good_proxys)
                        print(f'bulk_insert ips to db')
                        # 6 更新ips_cycle產生器 #################################
                        ips_cfg.ips_cycle = itertools.cycle(good_proxys)
                        #
                        get_freeproxy_cnt += 1
                        print(f'get_freeproxy 第{get_freeproxy_cnt}次更新成功:{now}')
                        print(f'good_proxys 數量: {len(good_proxys)}\n')
                    else:
                        pass
        except Exception as e:
            print(f"get_freeproxy: {repr(e)}")
        #
        if once:
            break


###############################################################################
tasks_list = [
    (get_freeproxy, [get_freeproxy_delta, False]),
    (ips_Queue_put, [2]),
]
###############################################################################


if __name__ == '__main__':
    try:
        from IPython import get_ipython
        tmp = 'zmqshell' in str(type(get_ipython()))  # 在jupyter
        print(tmp, '在jupyter')
    except Exception:
        loop = asyncio.get_event_loop()
        task = loop.create_task(get_freeproxy(1))
        loop.run_until_complete(task)
else:
    # print(__name__) # apps.ips.tasks
    if 0:
        asyncio.create_task(get_freeproxy(3, False))
