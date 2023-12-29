import os
#
from fastapi.templating import Jinja2Templates
#
##########################################################

#
login = {
    'email': 'mybigdata.001@gmail.com',
    'BOOKS': ['wtb0806', 'wtbcode0806'],
}

dt_format = "%Y-%m-%d_%H:%M:%S"
pub_dt_format = "%Y-%m-%d"
#
cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
#
timeout = 7
update_errcnt_max = 50  # 一本書的爬蟲次數
#
top_proxy_max = 100
objs_max = 200
del_store_objs_delta = 60 * 2
dt_format = "%Y-%m-%d_%H:%M:%S"
#
q_size = 3
days_without_update = 3
