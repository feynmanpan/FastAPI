import asyncio
import aiohttp
from pyquery import PyQuery as pq
import pandas as pd
import os
from typing import Any
#
import sqlalchemy as sa
from fastapi import Request
from fastapi.responses import HTMLResponse
#
from .config import (
    jinja_templates,
    ips_err_csv_path,
    ips_csv_path,
    ips_csv_tb_html,
    ips_html_path,
    ips_html,
)
from . import config as ips_cfg
from .model import IPS  # ,tb_ips
from .utils import CHECK_PROXY
from apps.sql.config import dbwtb
########################################################


async def get_next_ip():
    # 從cycle取一個ip port
    ips_cycle = ips_cfg.ips_cycle
    if ips_cycle:
        return next(ips_cycle)
    else:
        return '請啟動startBGT'


async def check_proxy():
    proxy_ip = '161.202.226.194'
    proxy_port = '80'
    #
    return await CHECK_PROXY(proxy_ip, proxy_port, '11').isGood()


async def show_freeproxy(request: Request, f: str = 'csv'):
    context: dict[str, Any] = {
        'request': request,
    }
    rep = HTMLResponse('請啟動startBGT，撈取csv')
    if f == 'html':
        # 每次抓取的原始頁
        if os.path.isfile(ips_html_path):
            rep = jinja_templates.TemplateResponse(ips_html, context)
    elif f == 'err':
        # 顯示 ips_err
        if os.path.isfile(ips_err_csv_path):
            context['ips_csv_tb_html'] = pd.read_csv(ips_err_csv_path).to_html()
            rep = jinja_templates.TemplateResponse(ips_csv_tb_html, context)
    elif f == 'db':
        cs = [
            # IPS.idx,  # tb_ips.c.id,
            IPS.ip,  # tb_ips.c.ip,
            IPS.port,  # tb_ips.c.port,
            IPS.goodcnt,  # tb_ips.c.goodcnt,
        ]
        query = sa.select(cs)  # .order_by('idx', 'ip')  # .where(IPS.id > 100) .where(tb_ips.columns.id > 100)
        records = await dbwtb.fetch_all(query)
        #
        context['ips_csv_tb_html'] = pd.DataFrame([dict(r) for r in records]).to_html()
        rep = jinja_templates.TemplateResponse(ips_csv_tb_html, context)
    else:
        # 顯示持續擴充更新的csv
        if os.path.isfile(ips_csv_path):
            context['ips_csv_tb_html'] = pd.read_csv(ips_csv_path).to_html()
            rep = jinja_templates.TemplateResponse(ips_csv_tb_html, context)
    #
    return rep
