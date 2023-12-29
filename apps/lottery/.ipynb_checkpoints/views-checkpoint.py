from .config import jinja_templates
from apps.lottery.lottery import LOTTERY
from apps.lottery.model import LOTTO
from apps.sql.config import dbwtb
from sqlalchemy import desc, asc
import sqlalchemy as sa
from fastapi import Request
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse
import pandas as pd
#
import plotly
from plotly.offline import plot as pt
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
pio.renderers.default = "iframe"
#
##########################################################
async def showsuper(request: Request, n: int = 30, m: int = 2):
    if n <= 0 or n >= 500:
        n = 30    
    cs = LOTTO.__table__.columns
    w1 = LOTTO.name == LOTTERY.names.super
    query = sa.select(cs).where(w1).order_by(desc(LOTTO.no)).limit(n)
    rows = await dbwtb.fetch_all(query)
    #
    df_s = pd.DataFrame(rows)[LOTTERY.cols].sort_values(by='no').reset_index(drop=True)
    #
    if m < 1 or m > 6:
        m = 2
    x = df_s['ymd']
    y = df_s['area1']
    data = []
    for i in range(1, 1+m):
        k = f'd{i}'
        j = (i-1)*3
        v = go.Scatter(x=x, y=y.str[j:j+2].astype(int))
        data.append(v)

    div = pt(data, output_type='div')
    #
    context = {
        'request': request,
        'div': div,
    }
    #
    return jinja_templates.TemplateResponse('show.html', context)