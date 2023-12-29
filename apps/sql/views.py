from fastapi.responses import HTMLResponse
import pandas as pd
#
import apps.sql.config as sqlcfg
from apps.sql.config import r_redis
####################################################


def dbwtb_isconnected():
    """確認db連線"""
    msg = f"dbwtb_isconnected= {sqlcfg.dbwtb.is_connected}"
    return HTMLResponse(msg)


def redis_kv():
    """redis kv"""
    kv = []
    for k in r_redis.scan_iter():
        kv.append([k, r_redis[k]])
    #
    df = pd.DataFrame(kv).set_axis(['k', 'v'], axis=1)
    tb = df.to_html()
    #
    html = '''
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            table, td, th {
                border: 1px solid black;
                padding: 5px;
            }

            table {
                border-collapse: collapse;
            }
        </style>
        </head>
        <body>
        ''' + tb +\
        '''
        </body>
        </html>
        '''
    return HTMLResponse(html)
