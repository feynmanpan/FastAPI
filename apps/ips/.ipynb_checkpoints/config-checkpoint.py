import os
import itertools
import asyncio
#
from fastapi.templating import Jinja2Templates
########################################################
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
}
#
url_free = [
    "https://www.sslproxies.org/",
    'https://free-proxy-list.net/',
    'https://www.us-proxy.org/',
]
url_free_cycle = itertools.cycle(url_free)
level_https = [
    ('anonymous', 'yes'),
    ('elite proxy', 'yes'),
    ('anonymous', 'no'),
    ('elite proxy', 'no'),
]
get_freeproxy_delta = 4 * 60
timeout = 15
proxy_checkurls = [
    "http://210.240.175.62/NTIIS/IP_test.asp",
    "https://whatismyipaddress.com/zh-cn/index",
    "https://httpbin.org/ip",
    "https://www.whatismyip.com.tw/tw/",
    "https://www.whatismyip.com/",
    "https://www.rus.net.tw/myip.php",
    "https://www.myip.com/",
]
sampleN = len(proxy_checkurls)
check_atleast = 1
#
cacert = bool(1)
#
cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
# ______________________________________
ips_csv = 'ips.csv'
ips_html = 'ips.html'
ips_csv_tb_html = 'ips_csv_tb.html'
ips_err_csv = 'ips_err.csv'
#
ips_csv_path = os.path.join(cwd, ips_csv)
ips_err_csv_path = os.path.join(cwd, ips_err_csv)
ips_html_path = os.path.join(cwd, templates, ips_html)
#
ips_cycle = False  # 在task時有用來定義起始時間，所以不用None
ips_Queue = asyncio.Queue(1)
# ______________________________________
dtype = {'port': str}
dt_format = "%Y-%m-%d_%H:%M:%S"
ipcols = ['ip', 'port', 'now']
ipcols_err = ['ip', 'port', 'err']
maxN = 500
