import asyncio
import typing
from .config import jinja_templates
from apps.lottery.lottery import LOTTERY
from apps.lottery.model import LOTTO
from apps.sql.config import dbwtb
from sqlalchemy import desc, asc
import sqlalchemy as sa
from fastapi import Request
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse
import pandas as pd
import numpy as np
import random
from typing import Tuple
#
import plotly
from plotly.offline import plot as pt
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
pio.renderers.default = "iframe"
#
########################################################


async def df_fromDB(name: str = LOTTERY.names.super, db=dbwtb):
    '''回傳開獎順序/大小順序'''
    # cs = LOTTO.__table__.columns
    cs = [
        LOTTO.ymd,
        LOTTO.area1,
        LOTTO.area1asc,
        LOTTO.area2,
        LOTTO.salesamount,
        LOTTO.totalbonus,
    ]
    w1 = LOTTO.name == name
    query = sa.select(cs).where(w1)  # .order_by(desc(LOTTO.ymd)).limit(n)
    rows = await db.fetch_all(query)
    # _________________________________________________________________
    df = pd.DataFrame(rows).sort_values(by='ymd', ascending=True).reset_index(drop=True).rename(columns={'area2': 6})
    df_area1 = df.area1.str.rsplit("_", expand=True)
    df_area1asc = df.area1asc.str.rsplit("_", expand=True)
    # df.columns = ymd, salesamount, totalbonus, 6, 012345
    tmp = df[['ymd', 'salesamount', 'totalbonus', 6]]
    df = pd.concat([tmp, df_area1], axis=1)  # 開獎順序
    dfasc = pd.concat([tmp, df_area1asc], axis=1)  # 大小順序
    #
    return df, dfasc


def overview_fromdf(df, n, m, legend_title='開獎順序', getmean=False):
    x = df['ymd'][-n:]
    data = []
    #
    for i in range(m):
        y = df[i][-n:].astype(int)
        v = go.Scatter(x=x, y=y, name=f'{i==6 and "第二區" or f"第{i+1}球"}')
        data.append(v)
    #
    if getmean:
        y = df[range(6)][-n:].astype(int).mean(axis=1).round().astype(int)
        v = go.Scatter(x=x, y=y, name=f'六球平均')
        data.append(v)
    #
    fig_overview = go.Figure(
        data=data,
        layout=go.Layout(
            title=go.layout.Title(text=f"威力彩最近{n}筆的開獎結果 (01~38, 01~08): 【{legend_title}】"),
            xaxis=go.layout.XAxis(title='開獎日期'),
            yaxis=go.layout.YAxis(title='號碼'),
            legend=go.layout.Legend(title=legend_title),
        )
    )
    #
    return pt(fig_overview, output_type='div')


def contour_fromdfasc(dfasc, n=50):
    '''等高線'''
    data = go.Contour(
        z=dfasc[-n:].T.loc[0:5, :].values,
        x=dfasc[-n:].ymd,
        y=list(range(1, 6)),  # vertical axis
        colorbar=dict(
            title='號碼顏色',  # title here
            titleside='right',
            titlefont=dict(
                size=14,
                family='Arial, sans-serif')
        )
    )
    #
    fig_contour = go.Figure(
        data=data,
        layout=go.Layout(
            title=go.layout.Title(text=f"威力彩最近{n}筆的第一區大小順序等高圖: 以顏色代表號碼"),
            xaxis=go.layout.XAxis(title='開獎日期'),
            yaxis=go.layout.YAxis(title='大小順序'),
        )
    )
    #
    return pt(fig_contour, output_type='div')


def recommend(dfasc) -> Tuple[list, int]:
    '''兩區推薦'''
    # six = dfasc[range(6)].astype(int).mean().astype(int).tolist()
    # six2 = sorted(random.sample(range(1, 39), 6))
    # a1 = [(a + b) // 2 for a, b in zip(six, six2)]
    data = []
    cnt = 1000
    for i in range(cnt):
        data.append(sorted(random.sample(range(1, 39), 6)))
    #
    df = pd.DataFrame(data).append(dfasc[range(6)].astype(int)).reset_index(drop=True)
    nums = []
    for c in df.columns:
        n = random.choice(df[c])
        if n in nums:
            n = max(nums) + 1
        nums.append(n)
        nums = sorted(nums)
    #
    return nums, random.randrange(1, 9)

########################################################


async def showsuper(request: Request, n: int = 100, m: int = 7):
    '''威力彩'''
    # DB 全抓 _________________________________________________________________
    df, dfasc = await df_fromDB(LOTTERY.names.super)

    ###################################################################
    # 兩區推薦
    a1, a2 = recommend(dfasc)
    ###################################################################
    # 最近n筆開獎，顯示球數
    n = (1 <= n <= 500) and n or 100
    m = (1 <= m <= 7) and m or 7
    #
    overview = overview_fromdf(df, n, m, '開獎順序')
    overview_asc = overview_fromdf(dfasc, n, m, '大小順序', True)
    contour_asc = contour_fromdfasc(dfasc, n)
    ###################################################################
    # 下次第一球
    b1 = df[0]
    # b11 = b1[1:].reset_index(drop=True)
    b11 = b1.shift(-1)
    b1_ = pd.concat([b1, b11], axis=1).set_axis(['本期開獎第1球', '下期開獎第1球'], axis=1).dropna().astype(int)
    b1_['下期'] = '號碼'
    b1_['size'] = 0.05
    avg = b1_.groupby('本期開獎第1球', as_index=False).mean().round().astype(int)
    avg['下期'] = '平均'
    avg['size'] = 0.3
    b1_ = pd.concat([b1_, avg])
    #
    fig_b1next = px.scatter(
        b1_, x="本期開獎第1球", y="下期開獎第1球",
        title='連續兩期開獎第一球之關係', color="下期", size='size'
    )
    #
    b1next = pt(fig_b1next, output_type='div')
    ###################################################################
    # 第一區各月份出現頻率最高之top2號碼
    df['m'] = df.ymd.str[4:6]  # 加月份
    cols = ['m', 0, 1, 2, 3, 4, 5]
    df_m = df[cols].astype(int).set_axis(list('mabcdef'), axis=1)
    df_m.loc[:, "a":"f"] = df_m.loc[:, "a":"f"].applymap(lambda x: [x])
    df_m = df_m.groupby('m').sum().sum(axis=1).to_frame().explode(0)
    df_m = df_m.reset_index().rename(columns={0: 'bn'}).astype(int).assign(cnt=1)  # bn 球號碼
    df_m = df_m.groupby(by=['m', 'bn'], as_index=False).sum().sort_values(by=['m', 'cnt'], ascending=[True, False]).groupby('m').head(2)
    df_m1 = df_m.groupby('m').head(1)
    df_m2 = df_m.groupby('m').tail(1)
    #
    fig_m = go.Figure(
        data=[
            go.Bar(x=df_m1.m, y=df_m1.cnt, text=df_m1.bn, textposition='auto', name='最高'),
            go.Bar(x=df_m2.m, y=df_m2.cnt, text=df_m2.bn, textposition='auto', name='次高')
        ],
        layout=go.Layout(
            title=go.layout.Title(text=f"歷年各月份第一區開出次數最高前兩名號碼(長條頂端數字)"),
            xaxis=go.layout.XAxis(title='開獎月份'),
            yaxis=go.layout.YAxis(title='開出次數'),
        )
    )
    fig_m.update_layout(barmode='group')
    #
    monthtop2 = pt(fig_m, output_type='div')
    ###################################################################
    # 歷年開獎順序的號碼大小起伏之開獎次數
    for i in range(5):
        col = f'{i}{i+1}'
        df[col] = df[i + 1].astype(int) - df[i].astype(int)
        df[col] = np.where(df[col] > 0, '/', '\\')
    tmp = df.loc[:, '01':].values.tolist()
    dfw = pd.Series(tmp).str.join('').value_counts().rename_axis('wave').reset_index(name='cnt')
    # dfw['pa'] = (100 * dfw.cnt / dfw.cnt.sum()).round(2)
    dfw.sort_values(by=['cnt'], ascending=True, inplace=True)
    #
    fig_wave = go.Figure(
        data=[
            go.Bar(x=dfw.cnt, y=dfw.wave, orientation='h'),
        ],
        layout=go.Layout(
            height=dfw.shape[0] * 23,
            showlegend=False,
            title=go.layout.Title(text=f"歷年依開獎順序的第一區號碼起伏之開獎次數(/為上升，\為下降)"),
            xaxis=go.layout.XAxis(title='開獎次數', side='top'),
            yaxis=go.layout.YAxis(title='起伏波形', tickmode='linear'),
        )
    )
    wave = pt(fig_wave, output_type='div')
    ###################################################################
    # 3D
    dff = df.copy()
    dff['第一區平均'] = dff[range(6)].astype(int).mean(axis=1).astype(int)
    dff['第一區標準差'] = dff[range(6)].astype(int).std(axis=1).astype(int)
    dff['第二區'] = dff[6].astype(int)
    n = 20
    dff['開獎第一球'] = np.where(dff[0].astype(int) > n, f'>{n}', f'<={n}')
    dff = dff[['開獎第一球', '第一區平均', '第一區標準差', '第二區']]
    #
    fig_3d = px.scatter_3d(
        dff,
        x="第一區平均",
        y='第一區標準差',
        z='第二區',
        color='開獎第一球',
    )
    fig_3d.update_traces(marker=dict(size=6))
    fig_3d.update_layout(
        margin=dict(l=200, r=0, b=0, t=0),
        legend=dict(
            yanchor="top", y=0.8,
            xanchor="left", x=0,
        ),
    )
    s3d = pt(fig_3d, output_type='div')
    ###################################################################
    # sankey，連續開獎兩球的組合
    cols = ['source', 'target']
    dff = df.loc[:, 0:5].astype(int)
    df_data = dff[[0, 1]].set_axis(cols, axis=1)
    for i in range(1, 5):
        df_data = df_data.append(dff[[i, i + 1]].set_axis(cols, axis=1))
    df_data = df_data.sort_values(by=cols).reset_index(drop=True)
    df_data['value'] = 1
    df_data = df_data.groupby(by=cols, as_index=False).count()
    # 取出現次數最高的下一球
    df_data = df_data.sort_values(by=['source', 'value'], ascending=[True, False]).groupby(by='source').head(1).reset_index(drop=True)
    # (1) nodes的索引處理
    df_s = df_data.source.rename_axis('idx').reset_index()
    df_t = df_data.target.sort_values().drop_duplicates().reset_index(drop=True).rename_axis('idx').reset_index()
    df_t['idx'] += len(df_s)
    #
    nodea = [{'node': idx, 'name': str(s)} for idx, s in df_s.values]
    nodeb = [{'node': idx, 'name': str(t)} for idx, t in df_t.values]
    nodes = nodea + nodeb
    # (2) links: source及target的索引處理
    df_data = df_data.merge(df_s, on=['source'], how='left').merge(df_t, on=['target'], how='left')[['idx_x', 'idx_y', 'value']]
    links = df_data.set_axis(cols + ['value'], axis=1).to_dict(orient='records')
    # (3)
    sankeydata = {
        "nodes": nodes,
        "links": links,
    }
    ###################################################################

    context = {
        'request': request,
        #
        # 'a1': a1,
        # 'a2': a2,
        'overview': overview,
        'overview_asc': overview_asc,
        'contour_asc': contour_asc,
        'b1next': b1next,
        'monthtop2': monthtop2,
        'wave': wave,
        's3d': s3d,
        'sankeydata': sankeydata,
    }
    #
    return jinja_templates.TemplateResponse('show.html', context)
