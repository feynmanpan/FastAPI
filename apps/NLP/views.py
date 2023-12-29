import os
#
from fastapi import Request, HTTPException
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
from middlewares import csrf_token_add, csrf_token_check

####################################################
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(cwd, gcp_key)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(cwd), gcp_key)  # os.path.join(cwd, gcp_key)


class postdata(BaseModel):
    text: str = 'testme'


@csrf_token_add
async def emotion(request: Request):
    context = {
        'request': request,
    }
    if os.path.isfile(emotion_path):
        rep = jinja_templates.TemplateResponse(emotion_html, context)
    else:
        rep = HTMLResponse(f'no {emotion_path}')
    #
    return rep


@csrf_token_check
async def emotion_handle(request: Request, data: postdata):
    '''用google處理文字的情緒指標'''
    print_func_name()
    #
    text = data.text
    # print(11111, data.__dict__)
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
        # response = client.classify_text(request={'document': document})
        response = client.classify_text(document=document)
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
