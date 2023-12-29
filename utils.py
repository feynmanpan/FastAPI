import sys
from os import path
import hashlib
import random
from random import shuffle
import string
from typing import Union
import datetime as dt
from datetime import datetime
from time import sleep
import json
#
import config
###############################################################################


def T_BeforeEveryDayHMS(
        H: int = 0,
        M: int = 0,
        S: int = 0,
        dt_format: str = config.dt_format) -> int:
    '''
        給定每天想執行的固定時分秒，計算當下還須等待多久seconds，或等待至隔天HMS
    '''
    now = datetime.now()
    nextday = now + dt.timedelta(days=1)
    # 今天及隔天的固定時分秒
    T1 = datetime.strptime(f"{now.date()}_{H}:{M}:{S}", dt_format)
    T2 = datetime.strptime(f"{nextday.date()}_{H}:{M}:{S}", dt_format)
    #
    T = (now <= T1) and T1 - now or T2 - now
    #
    return int(T.total_seconds())


def random_nstr(n: int = 10) -> str:
    '''隨機產生 n 個字元組合，包含 0-9, a-z, A-Z 中任一字元'''
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def hash_str(raw: Union[str, list], method: str = 'sha256') -> str:
    try:
        h = hashlib.__dict__[method]()
        raw = list(str(raw) + random_nstr() + random_nstr())
        shuffle(raw)
        h.update(''.join(raw).encode("utf-8"))
        result = h.hexdigest()
    except Exception as e:
        h = hashlib.sha256()
        h.update(random_nstr(20).encode("utf-8"))
        result = h.hexdigest()
    #
    return result


def print_func_name():
    '''取得執行print_func_name之函數名稱'''
    frame = sys._getframe()
    f_back = frame.f_back
    name = f_back and f_back.f_code.co_name or frame.f_code.co_name
    #
    print(f"\n\n執行函數:【{name}】")
    #
    return name


def static_makeornot(fn_static: str, fn_temp: str, context: dict):
    html_path_relative = path.join(config.static_html, fn_static)
    html_path_absolute = path.join(config.templates, html_path_relative)
    #
    if not path.exists(html_path_absolute):
        print(f'不存在，重造靜態檔: {html_path_absolute}')
        response = config.jinja_templates.TemplateResponse(fn_temp, context)
        with open(html_path_absolute, 'w') as f:
            f.write(response.body.decode('utf-8'))
    else:
        print(f'存在，直接回應靜態檔: {html_path_absolute}')
        response = config.jinja_templates.TemplateResponse(html_path_relative, context)
    #
    return response


class MSG:
    count = 0

    @classmethod
    def printmsg(cls, msg):
        cls.count += 1
        print(f'{cls.count}. {msg}')

    @classmethod
    def prt_msgs(cls, msgs: list):
        print("============================================================")
        for msg in msgs:
            cls.printmsg(msg)
        print("============================================================")


class CONST_BASE:
    '''
        class const(CONST_BASE):
            a:str # 沒有assign的一定要 type hint
            b = 1
        # 用法
        const.a == 'a' # 沒有assign的就直接用屬性名稱為value
        const.jsonstr == '{"b": 1, "a": "a"}'
    '''
    jsonstr = ''

    def __init_subclass__(cls):
        # 類別變數沒有assign的就直接用屬性名稱為value
        for k in cls.__annotations__:
            if k not in cls.__dict__:
                setattr(cls, k, k)
        # 將非內建的類別屬性key:value輸出json
        cls_dict = {k: v for k, v in cls.__dict__.items() if k[:2] != '__'}
        cls.jsonstr = json.dumps(cls_dict)
