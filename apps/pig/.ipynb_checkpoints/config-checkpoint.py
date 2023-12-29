from collections import namedtuple
import os
import aiohttp
#
from fastapi.templating import Jinja2Templates
###########################################################

# 規格豬
cacert = [False, True][1]
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
}
url_pig = "https://ppg.naif.org.tw/naif/MarketInformation/Pig/FPSCompare.aspx"
url_pig2 = "https://ppg.naif.org.tw/naif/MarketInformation/Pig/TranStatistics.aspx"  # 單日多市場價量比較
#
cwd = os.path.dirname(os.path.realpath(__file__))
dmy = ['d', 'm', 'y']
pig_csv_path = namedtuple('pig_csv', dmy)(*[os.path.join(cwd, f'pig_{tmp}.csv') for tmp in dmy])
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))

#
year_format = '%Y'
month_format = '%Y-%m'
date_format = '%Y-%m-%d'
time_format = '%H:%M:%S'
#
wd_map = {
    0: '(一)',
    1: '(二)',
    2: '(三)',
    3: '(四)',
    4: '(五)',
    5: '(六)',
    6: '(日)',
}

d_postdata = {
    '__VIEWSTATE': None,
    '__VIEWSTATEGENERATOR': None,
    '__EVENTVALIDATION': None,
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$TextBox_Content1_ThisDate': None,
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$TextBox_Content1_LastDate': None,
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$CheckBoxList_Market$1': 'H268',  # 宜蘭,新竹,苗栗,花蓮,澎湖,台灣地區，一次查
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$CheckBoxList_Market$3': 'H302',
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$CheckBoxList_Market$4': 'H356',
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$CheckBoxList_Market$20': 'H955',
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$CheckBoxList_Market$21': 'H880',  # 澎湖
    'ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$CheckBoxList_Market$22': '%',  # 台灣
    "ctl00$ctl00$ContentPlaceHolder_contant$ContentPlaceHolder_contant$Button_query": "查詢",
}
