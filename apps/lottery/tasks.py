import asyncio
from datetime import datetime
#
from apps.lottery.lottery import LOTTERY
from apps.lottery.config import(
    # delta_daily_get_lottery,
    daily_HMS,
    daily_thread,
)
#
from utils import T_BeforeEveryDayHMS
###############################################################################


async def daily_get_lottery(t):
    '''每日抓取三個開獎項目'''
    workers = [LOTTERY(name) for name in LOTTERY.names]
    #
    msg = 'daily_get_lottery: 還須等待{}秒，約{}分鐘，約{}小時'
    #
    while 1:
        # (1) 離HMS還很久時，就先sleep到夠近，直到30秒內 _____________________________________________
        if t is None:
            t = 5
            await asyncio.sleep(t)  # 第一次啟動，馬上抓
        else:
            t = T_BeforeEveryDayHMS(*daily_HMS)
            if t > daily_thread:
                print(msg.format(t, t // 60, t // 3600))
                await asyncio.sleep(t - daily_thread // 2)
                continue
        # (2) 執行爬蟲 _____________________________________________
        for w in workers:
            print(f'--------------開始 {w.name:>5} 的daily_get_lottery--------------')
            await w.getdata_in_ymrange()
            w.last_threevars = None
            # c = w.getdata_in_ymrange()
            # asyncio.create_task(c)
        # (3) 爬完強迫sleep夠久，超過今天HMS，避免短時間內重抓_____________________________________________
        t = T_BeforeEveryDayHMS(*daily_HMS)
        print(msg.format(t, t // 60, t // 3600))
        print('\n' * 3 + f'--------------結束 daily_get_lottery --------------' + '\n' * 3)
        await asyncio.sleep(60 * 5)


###############################################################################
tasks_list = [
    (daily_get_lottery, [None]),
]
###############################################################################
