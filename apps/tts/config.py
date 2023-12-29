import os
from fastapi.templating import Jinja2Templates
########################################################

cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
#
folder_pptx = 'pptx'
folder_pptx_path = os.path.join(cwd, folder_pptx)
tts_pptx_html = 'tts_pptx.html'
tts_pptx_path = os.path.join(cwd, templates, tts_pptx_html)
#
gcp_key = 'conda-20210806-key.json'
