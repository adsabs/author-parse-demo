#!/proj/adsx/author_parsing/bin/python2.6

import site
from os.path import abspath, dirname
os.environ['PYTHON_EGG_CACHE'] = dirname(abspath(__file__)) + '/.egg-cache'
site.addsitedir(dirname(abspath(__file__))))
site.addsitedir(dirname(abspath(__file__))) + '/lib/python2.6/site-packages')

from wsgiref.handlers import CGIHandler
from parse import app

CGIHandler().run(app)
