import os
from fastapi import Request, File, UploadFile
from fastapi.responses import HTMLResponse, ORJSONResponse, PlainTextResponse
import aiofiles
from config import top_dir, static
from .config import (
    cwd, gcp_key,
    jinja_templates,
    tts_pptx_path,
    tts_pptx_html,
    folder_pptx_path,
)
from .AnnotatePptx import TextToSpeech, Powerpoint
from middlewares import csrf_token_add, csrf_token_check
####################################################

# export GOOGLE_APPLICATION_CREDENTIALS="/home/pan/django_projects/fast_api_392/TTS/conda-20210806-key.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(cwd), gcp_key)  # os.path.join(cwd, gcp_key)


@csrf_token_add
async def tts_pptx(request: Request):
    context = {
        'request': request,
    }
    if os.path.isfile(tts_pptx_path):
        rep = jinja_templates.TemplateResponse(tts_pptx_html, context)
    else:
        rep = HTMLResponse(f'no {tts_pptx_path}')
    #
    return rep


@csrf_token_check
async def tts_pptx_handle(request: Request, file: UploadFile = File(...)):
    '''處理TTS'''
    fn = file.filename
    fn_out = fn.replace(".pptx", "_out.pptx")
    fn_path = os.path.join(folder_pptx_path, fn)
    fn_out_path = os.path.join(top_dir, static, 'tts', fn_out)
    result = None
    #
    try:
        # 先存
        async with aiofiles.open(fn_path, 'wb') as save_file:
            content = await file.read()  # async read
            if isinstance(content, str):
                content = content.encode('utf-8')
            await save_file.write(content)  # async write
        # 再轉
        t2s = TextToSpeech(gender='female', language='cmn-tw', speed=0.97)
        pp = Powerpoint(fn_path, t2s)
        pp.VoiceAnnotatePP(fn_out_path)
    except Exception as e:
        result = {
            'success': 0,
            'err': repr(e)
        }
    else:
        while not os.path.isfile(fn_out_path):
            pass
        result = {
            'success': 1,
            'fn_out': fn_out
        }
    finally:
        for filename in os.listdir(folder_pptx_path):
            tmp = os.path.join(folder_pptx_path, filename)
            if os.path.isfile(tmp) and 'pptx' not in filename:
                os.remove(tmp)
        #
        return ORJSONResponse(result)
