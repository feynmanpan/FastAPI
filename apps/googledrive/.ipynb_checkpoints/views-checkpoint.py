from fastapi import Request
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse
from .upload import upload


async def uploadgd(request: Request):
    '''上傳到雲端硬碟的parents目錄'''
    success, text = upload()
    #
    return PlainTextResponse(text)
