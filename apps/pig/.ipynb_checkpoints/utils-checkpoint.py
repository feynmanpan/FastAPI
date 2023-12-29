from time import sleep, time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests
import asyncio
import aiohttp
from pyquery import PyQuery as pq
import os
from os import path
from random import random, uniform
#
from .config import (
    cwd,
    date_format, month_format, year_format, wd_map,
    cacert, headers,
    url_pig, url_pig2,
    d_postdata,
)


def write_file(fpath, text):
    with open(fpath, 'w') as f:
        f.write(text)


def zero(x):
    return x != 0 and x or 0


def floatint(x):
    x = str(x).replace(',', '').replace('-', '0').replace(' ', '')
    x = x or '0'
    xf = float(x)
    xn = int(xf)
    return xf > xn and xf or xn


def isocheck(sd: str, ed: str, ymd_format: str):
    err = 'error'
    # (1) iso格式檢查
    try:
        datetime.strptime(sd, ymd_format)
        datetime.strptime(ed, ymd_format)
    except Exception:
        return False, {err: '日期格式非ISO標準，如2021-01-02，或日期數字過大過小不正常'}
    #
    print(f'sd={sd}, ed={ed}')
    # (2) 日期範圍檢查
    today = datetime.today().date()
    last_d = str(today - relativedelta(days=1))
    last_m = str(today - relativedelta(months=1))[:7]
    last_y = str(today - relativedelta(years=1))[:4]
    if ymd_format == date_format and ed > last_d:
        return False, {err: f'結束最晚到昨天{last_d}'}
    elif ymd_format == month_format and ed > last_m:
        return False, {err: f'結束最晚到上個月{last_m}'}
    elif ymd_format == year_format and ed > last_y:
        return False, {err: f'結束最晚到去年{last_y}'}
    #
    if sd > ed:
        return False, {err: f'開始需早於結束'}
    #
    return True, None


def df_miss_7595(df_miss):
    '''
        兩種標準之計算
    '''
    # 九個欄位: 台灣地區扣掉澎湖
    # cols = ['1', '2', '3', '75', '7595', '95115', '115135', '135155', '155']
    small = 0.0000012345
    ym = len(df_miss['date'][0]) <= 7
    cols = ['75', '7595', '95115', '115135', '135155', '155']  # 日行情時，75以前的欄位不做計算，由價量比較網頁值直接填入
    # (1)成交頭數 A 處理==================================================
    for col in cols:
        df_miss[f'A{col}'] = df_miss[f'A{col}']-df_miss[f'P{col}_A']
    if ym:
        df_miss['A3'] = df_miss['A3_tw']-df_miss['P3_A']
    # 不含澎湖的規格豬頭數計算
    df_A75 = df_miss.loc[:, 'A7595':'A135155']
    df_A155 = df_miss.loc[:, 'A155A':'A155D']
    # 兩種標準計算
    df_miss['A375'] = df_A75.sum(axis=1) + df_A155.sum(axis=1)
    df_miss['A395'] = df_miss['A375'] - df_miss['A7595']

    # (2)平均重量 B 處理==================================================
    for col in cols:
        T_weight = (df_miss[f'A{col}'] + df_miss[f'P{col}_A'])*df_miss[f'B{col}']
        P_weight = df_miss[f'P{col}_A']*df_miss[f'P{col}_B']
        #
        df_miss[f'B{col}'] = (T_weight - P_weight)/df_miss[f'A{col}'].replace(0, small)
    if ym:
        T_weight = df_miss['A3_tw']*df_miss['B3_tw']
        P_weight = df_miss['P3_A']*df_miss['P3_B']
        df_miss['B3'] = (T_weight-P_weight)/df_miss['A3'].replace(0, small)
    # 不含澎湖的規格豬平均重量計算
    df_A75 = df_miss.loc[:, 'A7595':'A135155']
    df_B75 = df_miss.loc[:, 'B7595':'B135155']
    df_A95 = df_miss.loc[:, 'A95115':'A135155']
    df_B95 = df_miss.loc[:, 'B95115':'B135155']
    df_A155 = df_miss.loc[:, 'A155A':'A155D']
    df_B155 = df_miss.loc[:, 'B155A':'B155D']
    # 以A區塊的欄名統一，之後相乘
    df_B75.columns = df_A75.columns
    df_B95.columns = df_A95.columns
    df_B155.columns = df_A155.columns
    # 兩種標準計算
    tmp75 = (df_A75 * df_B75).sum(axis=1)
    tmp95 = (df_A95 * df_B95).sum(axis=1)
    tmp155 = (df_A155 * df_B155).sum(axis=1)
    df_miss['B375'] = (tmp75 + tmp155) / df_miss['A375'].replace(0, small)
    df_miss['B395'] = (tmp95 + tmp155) / df_miss['A395'].replace(0, small)

    # (3)成交價格 C 處理==================================================
    for col in cols:
        P_weight = df_miss[f'P{col}_A']*df_miss[f'P{col}_B']
        P_total = P_weight*df_miss[f'P{col}_C']
        #
        T_weight = df_miss[f'A{col}']*df_miss[f'B{col}'] + P_weight
        T_total = T_weight*df_miss[f'C{col}']
        #
        df_miss[f'C{col}'] = (T_total - P_total)/(T_weight - P_weight).replace(0, small)
    if ym:
        P_weight = df_miss['P3_A']*df_miss['P3_B']  # 澎湖規格豬總重
        P_total = P_weight*df_miss['P3_C']  # 澎湖規格豬總金額
        #
        T_weight = df_miss['A3_tw']*df_miss['B3_tw']
        T_total = T_weight*df_miss['C3_tw']
        #
        df_miss['C3'] = (T_total - P_total)/(T_weight - P_weight).replace(0, small)
    #
    # 不含澎湖的規格豬平均價格計算
    df_A75 = df_miss.loc[:, 'A7595':'A135155']
    df_B75 = df_miss.loc[:, 'B7595':'B135155']
    df_C75 = df_miss.loc[:, 'C7595':'C135155']
    df_A95 = df_miss.loc[:, 'A95115':'A135155']
    df_B95 = df_miss.loc[:, 'B95115':'B135155']
    df_C95 = df_miss.loc[:, 'C95115':'C135155']
    df_A155 = df_miss.loc[:, 'A155A':'A155D']
    df_B155 = df_miss.loc[:, 'B155A':'B155D']
    df_C155 = df_miss.loc[:, 'C155A':'C155D']
    # 以A區塊的欄名統一，之後相乘
    df_B75.columns = df_A75.columns
    df_C75.columns = df_A75.columns
    df_B95.columns = df_A95.columns
    df_C95.columns = df_A95.columns
    df_B155.columns = df_A155.columns
    df_C155.columns = df_A155.columns
    # 兩種標準計算
    tmp75 = (df_A75 * df_B75 * df_C75).sum(axis=1)
    tmp95 = (df_A95 * df_B95 * df_C95).sum(axis=1)
    tmp155 = (df_A155 * df_B155 * df_C155).sum(axis=1)
    df_miss['C375'] = (tmp75 + tmp155) / (df_miss['A375']*df_miss['B375']).replace(0, small)
    df_miss['C395'] = (tmp95 + tmp155) / (df_miss['A395']*df_miss['B395']).replace(0, small)
    #
    if ym:
        df_miss['C375D'] = df_miss['C375'] - df_miss['C3']
        df_miss['C395D'] = df_miss['C395'] - df_miss['C3']
    # (4)155以上 total處理==================================================
    df_miss['A155ABCD'] = df_A155.sum(axis=1)
    df_miss['B155ABCD'] = (df_A155 * df_B155).sum(axis=1)/df_miss['A155ABCD'].replace(0, small)
    df_miss['C155ABCD'] = (df_A155 * df_B155 * df_C155).sum(axis=1)/(df_miss['A155ABCD']*df_miss['B155ABCD']).replace(0, small)
    #
    return df_miss


async def aio_get(session, url: str):
    async with session.get(url, headers=headers) as r:
        return await r.text(encoding='utf8')


async def aio_post(session, url: str, postdata):
    async with session.post(url, headers=headers, data=postdata) as r:
        return await r.text(encoding='utf8')


async def get_single_d(D: str):
    stime = time()
    await asyncio.sleep(uniform(0.1, 1))
    # 每個session重造connector
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=cacert)) as session:
        # (1)第一次進入頁面
        r1 = await aio_get(session, url_pig)
        doc1 = pq(r1, parser='html')
        #
        update = {
            '__VIEWSTATE': doc1.find("#__VIEWSTATE").attr('value'),
            '__VIEWSTATEGENERATOR': doc1.find("#__VIEWSTATEGENERATOR").attr('value'),
            '__EVENTVALIDATION': doc1.find("#__EVENTVALIDATION").attr('value'),
            'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$TextBox_Content1_ThisDate': D,
            'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$TextBox_Content1_LastDate': D,
        }
        postdata = {**d_postdata, **update}
        # (2)開始查詢送出表單
        r2 = await aio_post(session, url_pig, postdata)
        doc2 = pq(r2, parser='html')
        # 抓13列
        trs = doc2.find('.tbResult').find('tr')
        # 宜蘭,新竹,苗栗,花蓮的155以上
        tr11 = trs.eq(11).find('td')
        tr28 = trs.eq(28).find('td')
        tr45 = trs.eq(45).find('td')
        tr62 = trs.eq(62).find('td')
        # 澎湖
        tds71 = trs.eq(71).find('td')
        tds72 = trs.eq(72).find('td')
        tds73 = trs.eq(73).find('td')
        tds74 = trs.eq(74).find('td')
        tds75 = trs.eq(75).find('td')
        tds76 = trs.eq(76).find('td')
        tds77 = trs.eq(77).find('td')
        tds78 = trs.eq(78).find('td')
        tds79 = trs.eq(79).find('td')
        # 台灣地區
        # tds88 = trs.eq(88).find('td')
        # tds89 = trs.eq(89).find('td')
        # tds90 = trs.eq(90).find('td')
        tds91 = trs.eq(91).find('td')
        tds92 = trs.eq(92).find('td')
        tds93 = trs.eq(93).find('td')
        tds94 = trs.eq(94).find('td')
        tds95 = trs.eq(95).find('td')
        tds96 = trs.eq(96).find('td')
        #
        today = {
            'date': D,
            'wd': wd_map[datetime.strptime(D, date_format).weekday()],
            # A.成交頭數_______________________________
            # 'A1': tds88.eq(2).text(),
            # 'A2': tds89.eq(2).text(),
            # 'A3': tds90.eq(2).text(),
            'A1_tw@': '0',
            'A2@': '0',
            'A3_tw@': '0',
            'A3@': '0',
            #
            'A375': '0',  # 75+
            'A395': '0',  # 95+
            'A75': tds91.eq(2).text(),
            'A7595': tds92.eq(2).text(),
            'A95115': tds93.eq(2).text(),
            'A115135': tds94.eq(2).text(),
            'A135155': tds95.eq(2).text(),
            'A155': tds96.eq(2).text(),
            #
            'A155A': tr11.eq(2).text(),
            'A155B': tr28.eq(2).text(),
            'A155C': tr45.eq(2).text(),
            'A155D': tr62.eq(2).text(),
            'A155ABCD': '0',
            # B.平均重量_______________________________
            # 'B1': tds88.eq(5).text(),
            # 'B2': tds89.eq(5).text(),
            # 'B3': tds90.eq(5).text(),
            'B1_tw@': '0',
            'B2@': '0',
            'B3_tw@': '0',
            'B3@': '0',
            #
            'B375': '0',
            'B395': '0',
            'B75': tds91.eq(5).text(),
            'B7595': tds92.eq(5).text(),
            'B95115': tds93.eq(5).text(),
            'B115135': tds94.eq(5).text(),
            'B135155': tds95.eq(5).text(),
            'B155': tds96.eq(5).text(),
            #
            'B155A': tr11.eq(5).text(),
            'B155B': tr28.eq(5).text(),
            'B155C': tr45.eq(5).text(),
            'B155D': tr62.eq(5).text(),
            'B155ABCD': '0',
            # C.成交價格_______________________________
            # 'C1': tds88.eq(8).text(),
            # 'C2': tds89.eq(8).text(),
            # 'C3': tds90.eq(8).text(),
            'C1_tw@': '0',
            'C2@': '0',
            'C3_tw@': '0',
            'C3@': '0',
            #
            'C375': '0',
            'C395': '0',
            'C375D': '0',
            'C395D': '0',
            'C75': tds91.eq(8).text(),
            'C7595': tds92.eq(8).text(),
            'C95115': tds93.eq(8).text(),
            'C115135': tds94.eq(8).text(),
            'C135155': tds95.eq(8).text(),
            'C155': tds96.eq(8).text(),
            #
            'C155A': tr11.eq(8).text(),
            'C155B': tr28.eq(8).text(),
            'C155C': tr45.eq(8).text(),
            'C155D': tr62.eq(8).text(),
            'C155ABCD': '0',
            # P.澎湖的9列數據=========================================
            'P1_A': tds71.eq(2).text(),
            'P2_A': tds72.eq(2).text(),
            'P3_A': tds73.eq(2).text(),
            'P75_A': tds74.eq(2).text(),
            'P7595_A': tds75.eq(2).text(),
            'P95115_A': tds76.eq(2).text(),
            'P115135_A': tds77.eq(2).text(),
            'P135155_A': tds78.eq(2).text(),
            'P155_A': tds79.eq(2).text(),
            #
            'P1_B': tds71.eq(5).text(),
            'P2_B': tds72.eq(5).text(),
            'P3_B': tds73.eq(5).text(),
            'P75_B': tds74.eq(5).text(),
            'P7595_B': tds75.eq(5).text(),
            'P95115_B': tds76.eq(5).text(),
            'P115135_B': tds77.eq(5).text(),
            'P135155_B': tds78.eq(5).text(),
            'P155_B': tds79.eq(5).text(),
            #
            'P1_C': tds71.eq(8).text(),
            'P2_C': tds72.eq(8).text(),
            'P3_C': tds73.eq(8).text(),
            'P75_C': tds74.eq(8).text(),
            'P7595_C': tds75.eq(8).text(),
            'P95115_C': tds76.eq(8).text(),
            'P115135_C': tds77.eq(8).text(),
            'P135155_C': tds78.eq(8).text(),
            'P155_C': tds79.eq(8).text(),
        }
        print(f'爬取 {D} 之日行情 OK,{time()-stime}')
        return today


async def get_single_d_T(D: str):
    '''【交易行情統計】'''
    stime = time()
    await asyncio.sleep(uniform(0.1, 1))
    #
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=cacert)) as session:
        # (1) 第一次進入頁面【交易行情統計】
        r1 = await aio_get(session, url_pig2)
        doc1 = pq(r1, parser='html')
        #
        postdata = {
            # 按下【單日多市場價量比較】
            '__EVENTTARGET': 'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$LinkButton_query2',
            '__VIEWSTATE': doc1.find("#__VIEWSTATE").attr('value'),
            '__VIEWSTATEGENERATOR': doc1.find("#__VIEWSTATEGENERATOR").attr('value'),
            '__EVENTVALIDATION': doc1.find("#__EVENTVALIDATION").attr('value'),
        }
        r2 = await aio_post(session, url_pig2, postdata)
        doc2 = pq(r2, parser='html')
        #
        await asyncio.sleep(uniform(0.1, 1))
        # 開始查詢
        postdata = {
            '__VIEWSTATE': doc2.find("#__VIEWSTATE").attr('value'),
            '__VIEWSTATEGENERATOR': doc2.find("#__VIEWSTATEGENERATOR").attr('value'),
            '__EVENTVALIDATION': doc2.find("#__EVENTVALIDATION").attr('value'),
            'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$Button_Content2_Submit': '查詢',
            'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$TextBox_Content2_QueryDate': D,
        }
        r3 = await aio_post(session, url_pig2, postdata)
        doc3 = pq(r3, parser='html')
        # 抓12個儲存格
        today = {
            'A1_tw@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label3_0').text(),  # 台灣合計成交頭數
            'A2@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label3_1').text(),  # 台灣(不含澎湖)合計成交頭數
            'A3_tw@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label6_0').text(),  # 台灣規格豬成交頭數
            'A3@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label6_1').text(),  # 不含澎湖之規格豬成交頭數
            #
            'B1_tw@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label4_0').text(),  # 台灣均重
            'B2@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label4_1').text(),  # 不含澎湖均重
            'B3_tw@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label8_0').text(),  # 台灣規格豬均重
            'B3@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label8_1').text(),  # 不含澎湖之規格豬均重
            #
            'C1_tw@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label5_0').text(),  # 台灣均價
            'C2@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label5_1').text(),  # 不含澎湖均價
            'C3_tw@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label10_0').text(),  # 台灣規格豬均價
            'C3@': doc3.find('#ContentPlaceHolder_contant_ContentPlaceHolder_contant_GridView2_Label10_1').text(),  # 不含澎湖之規格豬均價
        }
        print(f'爬取 {D} 之日行情 OK (單日多市場價量比較),{time()-stime}')
        #
        return today


async def get_miss_ds(miss_date: list):
    '''日行情'''
    # 開始查詢送出表單
    tasks = [asyncio.create_task(get_single_d(D)) for D in miss_date]
    tasks_T = [asyncio.create_task(get_single_d_T(D)) for D in miss_date]
    #
    day_data = await asyncio.gather(*tasks)
    day_data_T = await asyncio.gather(*tasks_T)
    #
    return day_data, day_data_T
