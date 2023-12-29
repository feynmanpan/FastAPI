import os
#
from fastapi.templating import Jinja2Templates
#
##########################################################
cwd = os.path.dirname(os.path.realpath(__file__))
templates = 'templates'
jinja_templates = Jinja2Templates(directory=os.path.join(cwd, templates))
#