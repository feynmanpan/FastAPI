import asyncio
import re
import time

#
from datetime import datetime, timezone
from io import StringIO

import boto3
import pandas as pd
import pytz

import apps.gameABB.config as cfg
from apps.gameABB.ABB import GAME, PLAYER


#
def get_now_tw():
    tw = pytz.timezone("Asia/Taipei")
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    now_tw = tw.normalize(now_utc.astimezone(tw))
    #
    return now_tw

def savetos3(ans="", histry="", s3=False):
    now = get_now_tw().strftime("%Y%m%d_%H%M%S")
    fn = f"dev/abb_log/auto/{ans}_{now}_auto.csv"
    #
    arr = re.findall('[0-9]{4}.[0-9]A[0-9]B', histry)
    df = pd.DataFrame(arr)[0].str.split('➜', expand=True).iloc[::-1]
    df = df.rename(columns={0: "guess", 1: "compare"})
    df = df.reset_index(drop=True)
    df['ans']=ans
    #
    if not s3:
        fn=f'./apps/gameABB/ai_histry/auto/{ans}_{now}.csv'
        df.to_csv(fn, index=False)
        return
    #
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    body = csv_buffer.getvalue()
    #
    s3 = boto3.resource("s3")
    bkn = "bk1234"
    bk1234 = s3.Bucket(bkn)    
    # 
    bk1234.put_object(Key=fn, Body=body)    


# ==========================================================================


async def auto_histry():
    """自猜自答"""
    _I = await PLAYER.creat()
    _ans = _I.randomsample()
    limit = 40
    #
    for i in range(limit):
        # await asyncio.sleep(0.1)
        # 太多次就強迫猜出，避免猜太久
        _aiguess = i == limit - 1 and _ans or _I.aiguess()
        # print(_aiguess)
        #
        _AB = GAME.compare(_ans, _aiguess)
        _result = cfg.result.format(_aiguess, _AB)
        _I.updateHistry(_result)
        if _AB == cfg.const.bingo:
            # print(f"bingo_auto: {_ans}",i+1)
            # savetos3(_ans, _I.histry)
            return i+1
    #