import os
#
from fastapi.templating import Jinja2Templates
#
##########################################################
cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
#
delta_daily_get_lottery = 2.5 * 60 * 60
daily_HMS = 23, 0, 0  # 每天晚上 23:00:00 抓一次樂透
daily_thread = 60
