from enum import Enum
import os
#
from fastapi.templating import Jinja2Templates
#
secret = 'P@$$w0rd'  # 重要path的prefix
#
top_dir = os.getcwd()
static = 'static'
templates = 'templates'
static_html = 'static_html'  # 在templates中的子目錄
pathABB = '/ABB'
#
jinja_templates = Jinja2Templates(directory=templates)


class MODES(Enum):
    maintenance = 1
    debug = 2
    prod = 3


now_mode = MODES(3)  # MODES.maintenance, MODES['maintenance'],  .name/.value
maintenance_allow_patterns = [
    '^/test/.+',
    '^/static/.+',
]
maintenance_html = 'maintenance.html'


#
dt_format = "%Y-%m-%d_%H:%M:%S"
#
global_TO = 10
middle_check_ipAuth = bool(1)
middle_check_isMT = bool(1)
middle_check_isTH = bool(1)
middle_check_isCORS = bool(1)
middle_header_add = bool(1)
middle_session_build = bool(1)
middle_global_timeout = bool(1)
#
allowed_all = ["*"]
# 避免client修改request中的DNS，進行 HTTP Host header attack，類似XSS。回應 Invalid host header
current_DNS = "wtb.ddns.net"
current_GCP = '35.234.3.167'
current_zero = '0.0.0.0'  # django打fastapi時的DNS
current_self = '127.0.0.1' # django打fastapi時的ip
current_rent = '123.193.60.165'  # 租屋處
current_lotong = '49.158.154.21' # 羅東無線網路
#
allowed_hosts = [
    current_DNS,
    current_GCP,
    current_zero,
    current_self,
#     "www.wtbwtb.ml",
#     "wtb.wtbwtb.tk",
"*",
     "abb.aws360.net",
    #"172.31.0.0/20",
    #"dev-76017888.ap-northeast-1.elb.amazonaws.com",
]
# 同源政策 CORS
# Server仍會處理跨域請求，所以簡單請求仍會造成Server被CSRF攻擊
# 只是藉由回應中的Access-Control-Allow-Origin
# 告訴瀏覽器: 回應只能讓允許的 allowed_origins 看。
https = "https://"
http = "http://"
allowed_origins = [
    f"{https}{current_DNS}",
#     f"{https}www.wtbwtb.ml",
#     f"{https}wtb.wtbwtb.tk",
    # "*",
]
#
ok_ips = [
    current_GCP,
    current_zero,
    current_self,
    current_rent,
    current_lotong,
    '1.200.96.7',
]
ban_ips = [
    # "220.138.234.58"
]


# True在main啟動時就執行
startBGT_atonce = bool(1)


###################### admin ###############################
DATABASE_URL = "postgres://pan:pgcode@localhost:5432/wtb"
REDIS_URL = "redis://root:redispwd@localhost:6379/0"
