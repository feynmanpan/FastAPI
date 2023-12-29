import os
import binascii
from fastapi import Request
from fastapi.responses import Response, FileResponse
from requests_toolbelt import MultipartEncoder
#
from .config import jinja_templates
#########################################


def encode_multipart_formdata(fields):
    boundary = binascii.hexlify(os.urandom(16)).decode('ascii')
    rn = "\r\n"
    #
    body = "".join(
        f"--{boundary}{rn}" +
        f"Content-Disposition: form-data; name=\"{field}\"{rn*2}" +
        f"{value}{rn}"
        for field, value in fields.items()
    ) + f"--{boundary}--{rn}"
    #
    content_type = f"multipart/form-data; boundary={boundary}"
    #
    return body, content_type


async def mp(request: Request, ajax:int=0):
    if not ajax:
        context = {
        'request': request,
        }
        return jinja_templates.TemplateResponse('show.html', context)
    else:
        cwd = os.path.dirname(os.path.realpath(__file__))
        path_file = os.path.join(cwd, 'mptest.jpg')
        #
        m = MultipartEncoder(
            fields={
                'msg': '{"success":1,"err":"nothing"}',
                'file': ('mptest.jpg', open(path_file,'rb'), 'image/jpg'),
            }
        )
        return Response(content=m.to_string(), media_type=m.content_type)

