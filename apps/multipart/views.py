import os
import json
import binascii
from fastapi import Request
from fastapi.responses import Response, FileResponse
from requests_toolbelt import MultipartEncoder
#
from .config import cwd, jinja_templates
################################################################


async def mp(request: Request, ajax: int = 0, suc: int = 1, err: str = 'nothing'):
    '''multipart response'''
    if not ajax:
        context = {
            'request': request,
            'suc': suc,
            'err': err,
        }
        return jinja_templates.TemplateResponse('show.html', context)
    else:
        path_file = os.path.join(cwd, 'mptest.jpg')
        #
        m = MultipartEncoder(
            fields={
                'msg': json.dumps({'success': suc, "err": err}),
                'file': ('mptest.jpg', open(path_file, 'rb'), 'image/jpg'),
            }
        )
        return Response(content=m.to_string(), media_type=m.content_type)
