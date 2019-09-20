# pyfup

<a href="https://github.com/drmats/pyfup/">
    <img
        src="https://raw.githubusercontent.com/drmats/pyfup/master/icon.png"
        align="left"
        hspace="10"
    >
</a>

Basic file upload WSGI application (python 2.6.x/2.7.x/3.3.x)

This script brings up a
[simple\_server](http://docs.python.org/3.3/library/wsgiref.html#module-wsgiref.simple_server)
from [python](http://python.org/)'s
[wsgiref](http://docs.python.org/3.3/library/wsgiref.html) package and runs
a **really simple** [WSGI](http://wsgi.org)
([PEP 3333](http://www.python.org/dev/peps/pep-3333/)) application on it.
It allows to upload any file using
[multipart/form-data](http://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.2)
form content type.
When [Document Object Model Events](http://www.w3.org/TR/DOM-Level-2-Events/events.html),
[Selectors API](http://www.w3.org/TR/selectors-api/),
[File API](http://www.w3.org/TR/FileAPI/),
[XMLHttpRequest](http://www.w3.org/TR/XMLHttpRequest/),
[XMLHttpRequestUpload](http://www.w3.org/TR/XMLHttpRequest/#xmlhttprequestupload)
and [FormData](http://www.w3.org/TR/XMLHttpRequest/#interface-formdata) are
available on the client side then upload process is performed with the usage
of client-side logic, allowing user to see the progress. Otherwise simple POST
request from within [HTML form](http://www.w3.org/TR/html401/interact/forms.html)
is performed.

**pyfup** doesn't depend on any external library - just vanilla python
environment is required.

Don't use it in production environment as it has not been reviewed
for security issues, however it's handy for ad-hoc file transfers
between machines over [HTTP protocol](http://www.ietf.org/rfc/rfc2616.txt).

[![GitHub top language](https://img.shields.io/github/languages/top/drmats/pyfup.svg)](https://github.com/drmats/pyfup)
[![GitHub code size](https://img.shields.io/github/languages/code-size/drmats/pyfup.svg)](https://github.com/drmats/pyfup)
[![GitHub tag](https://img.shields.io/github/tag/drmats/pyfup.svg)](https://github.com/drmats/pyfup)

```bash
$ python3 fup.py
[WSGIServer/0.2 CPython/3.6.5 pyfup/0.5.5]
listening on 0.0.0.0:8000 <192.168.1.13:8000>
```

<br />




## installation

No installation is necessary. Just
[download](https://raw.githubusercontent.com/drmats/pyfup/master/fup.py)
the latest version.

<br />




## usage

  * standalone:

    ```
    $ python fup.py --help
    usage: fup.py [-h] [-v] [--ssl] [-k KEY] [-c CERT] [-a AUTH] [--no-js]
                    [--use-sproxy] [--host HOST]
                    [port]

    Basic file upload WSGI application.

    positional arguments:
        port                  specify alternate port [default: 8000]

    optional arguments:
        -h, --help            show this help message and exit
        -v, --version         show program's version number and exit
        --ssl                 use SSL
        -k KEY, --key KEY     path to SSL key file
        -c CERT, --cert CERT  path to SSL certificate file
        -a AUTH, --auth AUTH  specify username:password that will be required from
                            user agent [default: no authentication required]
        --no-js               do not use JavaScript on client side
        --use-sproxy          use "sniffing" proxy for autodetect and switch to SSL
                            (EXPERIMENTAL FEATURE)
        --host HOST           specify host [default: 0.0.0.0]

    More at: https://github.com/drmats/pyfup
    ```


  * with [**werkzeug**](http://werkzeug.pocoo.org/):

    ```
    $ python -m werkzeug.serving [-b HOST:PORT] fup:app
    ```


  * with [**gunicorn**](http://gunicorn.org/):

    ```
    $ gunicorn [-b HOST] --access-logfile - fup:app
    ```


  * in order to be able to accept big files and avoid "worker timeouts" it is
  desirable to use asynchronous ([**eventlet**](http://eventlet.net/) or
  [**tornado**](http://www.tornadoweb.org/))
  [worker classes](http://docs.gunicorn.org/en/latest/settings.html#worker-processes):

    ```
    $ gunicorn [-b HOST] -k eventlet --access-logfile - fup:app
    $ gunicorn [-b HOST] -k gevent --access-logfile - fup:app
    $ gunicorn [-b HOST] -k tornado fup:app
    ```


  * with [**Twisted Web**](https://twistedmatrix.com/trac/wiki/TwistedWeb):

    ```
    $ twistd -n web [--port PORT] --wsgi fup.app
    ```


  * with [**uWSGI**](http://uwsgi-docs.readthedocs.org/en/latest/):

    ```
    $ uwsgi --plugin python --http :[PORT] --wsgi-file fup.py --callable app
    ```


  * with [**waitress**](http://docs.pylonsproject.org/projects/waitress/en/latest/):

    ```
    $ waitress-serve --port [PORT] fup:app
    ```

<br />




## notes on SSL

The easiest way to generate private key and self-signed certificate with
[**OpenSSL**](https://www.openssl.org/):

```
$ openssl req -newkey rsa:2048 -new -nodes -x509 -days 365 -keyout ssl.key -out ssl.cert
```

Beware that browser will complain that it can't confirm site's identity
and on first connection **pyfup** can log a request error
"SSLV3_ALERT_CERTIFICATE_UNKNOWN" (this behavior is user-agent dependent).

<br />




## support

You can support this project via [stellar][stellar] network:

* Payment address: [xcmats*keybase.io][xcmatspayment]
* Stellar account ID: [`GBYUN4PMACWBJ2CXVX2KID3WQOONPKZX2UL4J6ODMIRFCYOB3Z3C44UZ`][addressproof]

<br />




## license

**pyfup** is released under the BSD 2-Clause license. See the
[LICENSE](https://raw.githubusercontent.com/drmats/pyfup/master/LICENSE)
for more details.

<br />




## notes

The script was tested and is known to work with python versions 2.7.2, 2.7.3,
2.7.5, 3.3.0, 3.3.2 and 3.3.3 on linux and windows, but theoretically it should
work on all 2.6.x, 2.7.x and 3.3.x.




[stellar]: https://learn.stellar.org
[xcmatspayment]: https://keybase.io/xcmats
[addressproof]: https://keybase.io/xcmats/sigchain#d0999a36b501c4818c15cf813f5a53da5bfe437875d92262be8d285bbb67614e22
