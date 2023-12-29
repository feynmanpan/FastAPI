import asyncio
#
from apps.ips.tasks import tasks_list as ips_tasks
from apps.book.tasks import tasks_list as book_tasks
from apps.lottery.tasks import tasks_list as lotto_tasks
from apps.gameABB.auto_AI_histry import auto_histry
########################################################


async def check_task_exception(tasks):
    '''檢查task是否有exception而done'''
    await asyncio.sleep(0)
    L = '='
    Lrepeat = 30 * 2
    NL = '\n'
    L1 = f'{NL*5}{L*Lrepeat}{NL}'
    L2 = f'{NL}{L*Lrepeat}{NL*5}'
    err = '【Task 協程有問題】'
    OK = 'Task都沒問題'
    #

    while 1:
        await asyncio.sleep(10)
        e = [f"{t._coro.__name__} 發生: {repr(t._exception)}" for t in tasks if t._exception]
        if e:
            rep = f'{L1}{err+NL}{NL.join(e)}{L2}'
        else:
            rep = f'{L1}{OK}{L2}'
        #
        print(rep)
        # nset = set()
        # for t in asyncio.all_tasks():
        #     nset.add(t._coro.__name__)
        #     # if 'show' in t._coro.__name__:
        #     #     # if not st:
        #     #     #     st = t._loop.time()
        #     #     # if t._loop.time() - st > 11:
        #     #     t.cancel()
        # # print(t._coro.__name__, t._loop.time() - st, '\n' * 10)
        # print(nset)


async def loopme(t):
    cnt = 0
    # global ips_cycle
    while 1:
        await asyncio.sleep(t)
        # t += 1
        cnt += 1
        # ips_cycle = cnt
        print(f'cnt_1 = {cnt}')


async def loopme2(t):
    cnt = 0
    while 1:
        await asyncio.sleep(t)
        cnt += 1
        print(f'loopme2 = {cnt}')
        
async def do_auto_AI_histry(t):
    cnt = 0
    while 1:
        cnt += 1
        if cnt>=10001:
            print('stop do_auto_AI_histry')
            return
        await asyncio.sleep(t)
        await auto_histry()
        
        print(f'do_auto_AI_histry = {cnt}')        


#################### tasks_list ################################
tasks_list = [
    # (loopme, [1]),
    # (loopme2, [1]),
     # (do_auto_AI_histry, [1]),
    # ]
] #+\
   # lotto_tasks #+\
#     ips_tasks +\
#     book_tasks
