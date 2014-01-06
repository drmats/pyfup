# pyfup

Basic file upload WSGI application (python 2.x/3.x)

This script brings up a simple\_server from python's
[wsgiref](http://docs.python.org/3.3/library/wsgiref.html)
package and runs a really simple web application on it.
It allows to upload any file using multipart/form-data encoding.
Don't use it in production environment as it has not been
reviewed for security issues, however it's handy for ad-hoc
file transfers between machines over HTTP protocol.


## usage

    python fup.py [PORT]


## license

BSD 2-Clause


## notes

The script was tested and is known to work with python
versions 2.7.2, 2.7.3, 3.3.0, 3.3.2 and 3.3.3 on linux
and windows.
