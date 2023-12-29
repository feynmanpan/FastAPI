import asyncio
from datetime import datetime
#
from apps.lottery.lottery import LOTTERY

###############################################################################


async def daily_get_lottery(t):
    '''每日抓取三個開獎項目'''
    workers = [LOTTERY(name) for name in LOTTERY.names]
    while 1:
        await asyncio.sleep(t)
        #
        for w in workers:
            print(f'--------------開始 {w.name:>5} 的daily_get_lottery--------------')
            await w.getdata_in_ymrange()
            w.last_threevars = None
            # c = w.getdata_in_ymrange()
            # asyncio.create_task(c)
        #
        print('\n'*3+f'--------------結束 daily_get_lottery --------------'+'\n'*3)
        #         
        t = 2 * 60 * 60


###############################################################################
tasks_list = [
    (daily_get_lottery, [5]),
]
###############################################################################
