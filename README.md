# pyfup

Basic file upload WSGI application (python 2.x/3.x)

This script brings up a
[simple\_server](http://docs.python.org/3.3/library/wsgiref.html#module-wsgiref.simple_server)
from [python](http://python.org/)'s
[wsgiref](http://docs.python.org/3.3/library/wsgiref.html) package and runs
a **really simple** [WSGI](http://wsgi.org)
([PEP 3333](http://www.python.org/dev/peps/pep-3333/)) application on it.
It allows to upload any file using
[multipart/form-data](http://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2)
form content type.

Don't use it in production environment as it has not been
reviewed for security issues, however it's handy for ad-hoc
file transfers between machines over
[HTTP protocol](http://www.ietf.org/rfc/rfc2616.txt).




## installation

No installation is necessary. Just
[download](https://raw.github.com/drmats/pyfup/master/fup.py)
the latest version.




## usage

* stand alone:

        python fup.py [-h] [-v] [port]

* with [gunicorn](http://gunicorn.org/):
    
        gunicorn -b 0.0.0.0 --access-logfile - fup:app

* in order to be able to accept big files and avoid "worker timeouts" it is
desirable to use [eventlet](http://eventlet.net/),
[gevent](http://www.gevent.org/) or
[tornado](http://www.tornadoweb.org/)
[worker classes](http://docs.gunicorn.org/en/latest/settings.html#worker-processes):

        gunicorn -b 0.0.0.0 -k eventlet --access-logfile - fup:app
        gunicorn -b 0.0.0.0 -k gevent --access-logfile - fup:app
        gunicorn -b 0.0.0.0 -k tornado fup:app

* with [Twisted Web](https://twistedmatrix.com/trac/wiki/TwistedWeb):

        twistd -n web --port 8000 --wsgi fup.app




## license

**pyfup** is released under the BSD 2-Clause license. See the
[LICENSE](https://github.com/drmats/pyfup/blob/master/LICENSE)
for more details.




## notes

The script was tested and is known to work with python versions 2.7.2, 2.7.3,
2.7.5, 3.3.0, 3.3.2 and 3.3.3 on linux and windows.
