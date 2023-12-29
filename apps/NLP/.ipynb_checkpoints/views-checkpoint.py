import os
#
from fastapi import Request
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
#
from google.cloud import language_v1
from google.cloud.language_v1 import Document
from google.cloud.language_v1 import types
#
from apps.NLP.config import (
    cwd,
    gcp_key,
    jinja_templates,
    emotion_html,
    emotion_path,
)
from utils import print_func_name

####################################################
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(cwd, gcp_key)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(cwd), gcp_key)  # os.path.join(cwd, gcp_key)


class postdata(BaseModel):
    text: str
#     csrf_token: str


def emotion(request: Request):
    print(f"{request.session=}")
    request.session['id']='!@@@@'
#     
    context = {
        'request': request,
    }
    if os.path.isfile(emotion_path):
        rep = jinja_templates.TemplateResponse(emotion_html, context)
    else:
        rep = HTMLResponse(f'no {emotion_path}')
    #
    rep.set_cookie(key="csrftoken", value="123#45")
    print(f"{rep.headers=}")
#     print(f"{request.session=}")
    #     
    return rep


def emotion_handle(request: Request, data: postdata):
    '''用google處理文字的情緒指標'''
    print_func_name()
#     request.session['id']='!@@@@'
    print(f"{request.session=}")
    #
    text = data.text
#     csrf_token = data.csrf_token
    print(f"開始處理文字的情緒指標:__________\n{text}\n\n")
    # 實例化一個客戶端
    client = language_v1.LanguageServiceClient()
    # 要分析的文本
    document = types.Document(
        content=text,
        type_=Document.Type.PLAIN_TEXT,
    )
    # (1) 檢測文本的情緒
    sentiment = client.analyze_sentiment(document=document).document_sentiment
    # (2) 文本分類
    result_classify = {
        'err': '',
        'data': {},
    }
    try:
        response = client.classify_text(request={'document': document})
        categories = response.categories
        for category in categories:
            # Turn the categories into a dictionary of the form:
            # {category.name: category.confidence}, so that they can
            # be treated as a sparse vector.
            result_classify['data'][category.name] = category.confidence
    except Exception as e:
        result_classify['err'] = repr(e)

    # ________________________________________________________________
    result = {
        'score': sentiment.score,
        'magnitude': sentiment.magnitude,
        'result_classify': result_classify,
    }
    print(result)
    return ORJSONResponse(result)
