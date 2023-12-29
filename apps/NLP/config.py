import os
from fastapi.templating import Jinja2Templates
########################################################
# cwd = os.getcwd()
cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
#
emotion_html = 'emotion.html'
emotion_path = os.path.join(cwd, templates, emotion_html)
#
gcp_key = 'conda-20210806-key.json'
