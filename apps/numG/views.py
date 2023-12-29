from itertools import combinations, combinations_with_replacement
import json
from typing import Union
from fastapi import Request
from fastapi.responses import HTMLResponse
#
from .config import cwd, jinja_templates
####################################################################


def check(gi: Union[list, tuple, set]) -> bool:
    TF = True  # 滿足基本規則，任意兩元素之差不在群內
    if len(gi) > 1:
        for a, b in combinations(gi, 2):
            D = abs(a - b)
            if D in gi:
                TF = False
                break
    #
    return TF


def show_G(request: Request, S: int = 3):
    '''數字分三群'''
    if S < 3 or S > 13:
        S = 3
    # SN = set()  # 所有 x+a+b = S 的正整數解集合
    # for x in range(1, S):
    #     y = S - x
    #     if x < y:
    #         for a in range(1, y):
    #             b = y - a
    #             if a < b:
    #                 # 去重複解
    #                 e = json.dumps(sorted([x, a, b]))
    #                 SN.add(e)
    # #
    # SN = [json.loads(e) for e in SN]
    # SN = sorted(SN, key=lambda e: (e[0], e[1], e[2]))
    # __________________________________________________________
    # n類相異物中，任取r個為一組的重複組數: H(n,r)
    SN = []  # 所有 x+y+z = S 的正整數解集合，H(3,S)
    for tmp in combinations_with_replacement(range(3), S):
        sn = sorted([tmp.count(0), tmp.count(1), tmp.count(2)])
        if sn not in SN and all(sn):
            SN.append(sn)
    SN = sorted(SN, key=lambda e: (e[0], e[1], e[2]))
    # __________________________________________________________
    g123 = set(range(1, S + 1))
    ans = []
    cnt = 0
    for sn in SN:
        g1n, g2n, _ = sn  # 根據正整數解，取每群組合
        for g1 in combinations(g123, g1n):
            g23 = g123 - set(g1)
            for g2 in combinations(g23, g2n):
                g3 = g23 - set(g2)
                #
                g11 = json.dumps(sorted(g1))
                g22 = json.dumps(sorted(g2))
                g33 = json.dumps(sorted(g3))
                _g = set([g11, g22, g33])
                # 去重複+驗證基本規則
                if _g not in ans:
                    cnt += 1
                    if check(g1):
                        if check(g2):
                            if check(g3):
                                ans.append(_g)
    #
    for idx, _g in enumerate(ans):
        _g = [json.loads(gi) for gi in _g]
        ans[idx] = sorted(_g, key=lambda x: (len(x), x[0]))
    #
    ans = sorted(ans, key=lambda x: (len(x[0]), x[0][0], len(x[1]), x[1][0], len(x[2]), x[2][0]))
    #
    code = '''
        from itertools import combinations, combinations_with_replacement
        import json
        #
        def check(gi: Union[list, tuple, set]) -> bool:
            TF = True  # 滿足基本規則，任意兩元素之差不在群內
            if len(gi) != 1:
                for a, b in combinations(gi, 2):
                    D = abs(a - b)
                    if D in gi:
                        TF = False
                        break
            #
            return TF
        # _____________________________________
        if S < 3 or S > 13:
            S = 3
        # n類相異物中，任取r個為一組的重複組數: H(n,r)
        SN = []  # 所有 x+y+z = S 的正整數解集合，H(3,S)
        for tmp in combinations_with_replacement(range(3), S):
            sn = sorted([tmp.count(0), tmp.count(1), tmp.count(2)])
            if sn not in SN and all(sn):
                SN.append(sn)
        SN = sorted(SN, key=lambda e: (e[0], e[1], e[2]))
        # __________________________________________________________
        g123 = set(range(1, S + 1))
        ans = []
        cnt = 0
        for sn in SN:
            g1n, g2n, _ = sn  # 根據正整數解，取每群組合
            for g1 in combinations(g123, g1n):
                g23 = g123 - set(g1)
                for g2 in combinations(g23, g2n):
                    g3 = g23 - set(g2)
                    #
                    g11 = json.dumps(sorted(g1))
                    g22 = json.dumps(sorted(g2))
                    g33 = json.dumps(sorted(g3))
                    _g = set([g11, g22, g33])
                    # 去重複+驗證基本規則
                    if _g not in ans:
                        cnt += 1
                        if check(g1):
                            if check(g2):
                                if check(g3):
                                    ans.append(_g)
        #
        for idx, _g in enumerate(ans):
            _g = [json.loads(gi) for gi in _g]
            ans[idx] = sorted(_g, key=lambda x: (len(x), x[0]))
        #
        ans = sorted(ans, key=lambda x: (len(x[0]), x[0][0], len(x[1]), x[1][0], len(x[2]), x[2][0]))
    '''
    # _____________________________________
    context = {
        'request': request,
        'S': S,
        'ans': ans,
        'cnts': (cnt, len(ans)),
        'code': code,
    }
    return jinja_templates.TemplateResponse('show.html', context)
