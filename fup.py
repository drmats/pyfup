#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic file upload WSGI application (python 2.6.x/2.7.x/3.3.x).

This script brings up a simple_server from python's wsgiref package
and runs a really simple web application on it. It allows to upload
any file using multipart/form-data encoding. Don't use it in production
environment as it has not been reviewed for security issues, however
it's handy for ad-hoc file transfers between machines over HTTP protocol.

https://github.com/drmats/pyfup
"""

from __future__ import print_function, absolute_import

import os
import sys
import time
import signal
import base64
import gzip
import codecs
import re

from ntpath import basename as ntbasename
from posixpath import basename as posixbasename

from cgi import FieldStorage
from wsgiref.simple_server import (
    make_server,
    software_version,
    WSGIRequestHandler
)

__all__ = [
    "app",
    "Application",
    "FUPFieldStorage",
    "FUPRequestHandler",
    "GzipGlue",
    "Main",
    "Template",
    "utf8_encode",
    "View"
]

__author__ = "drmats"
__copyright__ = "copyright (c) 2014, drmats"
__version__ = "0.5.2"
__license__ = "BSD 2-Clause license"




# Python 3.2.x equivalent of gzip.compress and gzip.decompress
# for python 2.x.
class GzipGlue(object):

    """Gzip glue compat. layer for compress/decompress functions."""

    @staticmethod
    def _compress_p2 (s):
        """Emulates gzip.compress from python >=3.2."""
        osio = StringIO()
        try:
            if hasattr(gzip.GzipFile, "__exit__"):
                with gzip.GzipFile(fileobj=osio, mode="wb") as g:
                    g.write(s)
            else:
                g = gzip.GzipFile(fileobj=osio, mode="wb")
                g.write(s)
                g.close()
            return osio.getvalue()
        finally:
            osio.close()


    @staticmethod
    def _decompress_p2 (s):
        """Emulates gzip.decompress from python >=3.2."""
        isio = StringIO(s)
        try:
            if hasattr(gzip.GzipFile, "__exit__"):
                with gzip.GzipFile(fileobj=isio, mode="rb") as g:
                    return g.read()
            else:
                try:
                    g = gzip.GzipFile(fileobj=isio, mode="rb")
                    return g.read()
                finally:
                    g.close()
        finally:
            isio.close()


# based on a simple "feature detection" assign compress/decompress methods
if hasattr(gzip, "compress") and hasattr(gzip, "decompress"):
    GzipGlue.compress = staticmethod(gzip.compress)
    GzipGlue.decompress = staticmethod(gzip.decompress)
else:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO
    GzipGlue.compress = staticmethod(GzipGlue._compress_p2)
    GzipGlue.decompress = staticmethod(GzipGlue._decompress_p2)




# python 2.x lacks textwrap.indent function
from textwrap import dedent
try:
    from textwrap import indent
except ImportError:
    def indent (s, i):
        """Emulates texwrap.indent from python 3.x."""
        return "\n".join(map(
            lambda l:  i + l  if  l != ""  else  l,
            s.split("\n")
        ))




# python 2/3 unicode issues:
# Using "from __future__ import unicode_literals" statement in python 2.x
# is causing that all string literals are actually of type <type "unicode">
# therefore they should be encoded in all places which require type
# <type "str"> (e.g. "start_response" callback). But in python 3.x that
# approach results in type <class "bytes"> therefore TypeError is thrown.
# Unfortunately u"..." syntax is forbidden in python <3.3.x.
# So it's better to leave string literals at their default type behaviour
# in python 2.x/3.x but just handle the encoding. Python 2 defines "unicode"
# function for converting <type "str"> to <type "unicode"> which then behaves
# correctly while encoding back to "utf-8". Thus two definitions of 
# utf8_encode function below.
if hasattr(__builtins__, "unicode"):
    def utf8_encode (s, e="strict"):
        """python 2.x utf-8 encoder"""
        return unicode(s, "utf-8").encode("utf-8", e)
else:
    def utf8_encode (s, e="strict"):
        """python 3.x utf-8 encoder"""
        return s.encode("utf-8", errors=e)




# Static templates and assets.
class Template(object):

    """Markup definitions."""

    # default indent
    indent = " " * 4


    # common html head
    common_head = dedent("""\
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=Edge">
        <meta http-equiv="content-style-type" content="text/css">
        <link rel="icon" type="image/x-icon" href="favicon.ico">
        <title>pyfup</title>
        <link rel="stylesheet" type="text/css" href="m.css" media="screen">
    """)


    # default css
    css = dedent("""\
        @charset "utf-8";
        html {
            font-size: 14px;
            font-family: monospace;
            padding: 16px;
            line-height: 28px;
            background-color: #CCCCCC;
        }
        fieldset { border: none; height: 70px; }
        input { height: 30px; margin-bottom: 5px; }
        input.fselect { display: block; margin-top: 5px; width: 400px; }
        h2 {
            font-size: 20px;
            font-weight: bold;
            line-height: 20px;
            margin-bottom: 16px;
        }
        .logo {
            display: inline-block;
            width: 16px; height: 16px;
            margin: 2px 6px 2px 6px;
            background-image: url(favicon.ico);
            background-repeat: no-repeat;
            background-position: center center;
        }
        .progressFrame { height: 30px; line-height: 30px; opacity: 0; }
        .progressFrame .progressBar {
            float: left;
            width: 200px; height: 10px; margin: 10px;
            border: 1px solid black;
        }
        .progressFrame .progressBar .progress {
            width: 0px; height: 10px;
            background-color: #777777;
        }
        .progressFrame .percentage {
            float: left;
        }
        .message { clear: both;  margin-left: 10px; }
        a, a:visited { text-decoration: none; color: #0077CC; }
        a:hover { text-decoration: underline; }
        p { margin: 0px; padding: 0px; }"""
    )


    # gzipped and base64-encoded *.ico file
    favicon = GzipGlue.decompress(base64.b64decode(utf8_encode(dedent("""\
        H4sIAIRbzFIC/41UPWsiYRCe1bBGRAg5OAJXRNLERgvLC3KNlhZ+4AciWohEsBA\
        VrJSrbHIHd7/B+hovpeARKzurNDb3F7xgdFWYzLPJbjZx5RwZeZl35nHeZ56RSJ\
        HPyQnJt4+uj4g+EpFfXEISeY7vM2Ymt9ttnI+bzebnUqnUTaVSd4VC4RGeTqfvi\
        sVip9VqXUmOitx+v/8GZzabneXz+R/BYPDB6XQy4KyuqioHAoF/yWTyp2B8smKM\
        RqPTbDZ76/F4dureu9fr5Wg0+tvAkNqjdrt943K5/ltrxXjpQx0MBhfS80F1iqK\
        YZ7wFfPR6vW9GLBQKcTgcZofDYVsfi8XY5/OZfIDTRCJxb/Q0HA4ZJvGdWpmJfj\
        eZTMwY5iJcaAZeuVzm5XLJ2+2W6/W6mVetVnm1Wun1tVqNjflgtpFIRLP+TiaT0\
        fMWiwV3Oh2uVCr6GSYzetMT6uPx+L3dO2Hr9Zo1TdPPwvcOL9BYt9v9vo8r2Gaz\
        0fmwcg/HG6DT6XR66ff7bfkWfG40GrZ30Cm0nsvlHMLVDfg/VD/QKbSOfYEGx+P\
        xB5nFr0MwoFNoHfti3R9goI99b3npmaF17AtqsLfz+dzEwFvABzjFXDBb6AMag0\
        6hdeyLdfe3X4j+uoj+OIm+Ks9Ois0fhfJ6j1zUrM6JngCTkE5/fgQAAA=="""
    ))))


    # client javascript
    client_logic = dedent("""\
        /*global
            Date, document, File, FormData, Math,
            XMLHttpRequest, XMLHttpRequestUpload, window
        */
        /*jslint white: true */
        (function (u) {
            "use strict";
            u.onFsChange = function () { u.file = this.files.item(0); };
            u.replaceInput = function () {
                var ni;
                if (u.fs) {
                    u.fs.removeEventListener('change', u.onFsChange, false);
                    ni = document.createElement('input');
                    [
                        ['type', 'file'],
                        ['name', 'file'],
                        ['class', 'fselect']
                    ].forEach(function (attr) {
                        ni.setAttribute(attr[0], attr[1]);
                    });
                    u.fs.parentElement.replaceChild(ni, u.fs);
                } else {
                    ni = document.querySelector('.fselect');
                }
                ni.addEventListener('change', u.onFsChange, false);
                u.fs = ni;
            };
            u.init = function () {
                u.pf = document.querySelector('.progressFrame');
                u.pf.innerHTML =
                    '<div class="progressBar">' +
                        '<div class="progress"></div>' +
                    '</div>' +
                    '<div class="percentage">' +
                        '[<span class="p">0</span>%]' +
                    '</div>';
                u.progress = document.querySelector('.progress');
                u.p = document.querySelector('.p');
                u.replaceInput();
                u.submit = document.querySelector('input[type="submit"]');
                u.file = u.fs.files.item(0);
                u.message = document.querySelector('.message');
                u.submit.addEventListener('click', function (evt) {
                    evt.stopPropagation(); evt.preventDefault();
                    if (u.file) {
                        this.disabled = u.fs.disabled = true;
                        u.message.innerHTML = 'Uploading...';
                        u.pf.style.opacity = 1;
                        u.fd = new FormData();
                        u.fd.append('file', u.file);
                        u.xhr = new XMLHttpRequest();
                        u.xhr.addEventListener('load', function () {
                            u.submit.disabled = false;
                            u.replaceInput();
                            u.message.innerHTML =
                                '"' + u.file.name + '" ' +
                                '[' + (Math.floor(
                                    u.file.size / 1024 * 100
                                ) / 100) + 'kB]<br>' +
                                'uploaded successfully in ' +
                                Math.floor((u.now - u.start) / 1000) + 's!';
                            delete u.fd; delete u.xhr;
                            delete u.now; delete u.loaded; delete u.start;
                            u.file = null;
                            u.pf.style.opacity = 0;
                        }, false);
                        u.xhr.upload.addEventListener(
                            'progress',
                            function (e) {
                                var p, now, curRate, avgRate, time, eta;
                                if (e.lengthComputable) {
                                    now = Date.now();
                                    p = Math.floor(e.loaded/e.total*100);
                                    u.progress.style.width = (2*p) + 'px';
                                    u.p.innerHTML = p;
                                    curRate = Math.floor(
                                        (e.loaded - u.loaded) /
                                        ((now - u.now) / 1000) / 1024
                                    );
                                    avgRate = Math.floor(
                                        (e.loaded) /
                                        ((now - u.start) / 1000) / 1024
                                    );
                                    time = Math.floor(
                                        (now - u.start) / 1000
                                    );
                                    eta = Math.floor(
                                        (e.total - e.loaded) / avgRate / 1000
                                    );
                                    u.message.innerHTML =
                                        'Uploading... ' +
                                        Math.floor(e.loaded/1024) + 'kB / ' +
                                        Math.floor(e.total/1024) + 'kB<br>' +
                                        '[cur: ' + curRate + 'kB/s, ' +
                                        'avg: ' + avgRate + 'kB/s]<br>' +
                                        'elapsed time: ' + time + 's, ' +
                                        'time left: ' + eta + 's';
                                    u.now = now;
                                    u.loaded = e.loaded;
                                }
                            }, false
                        );
                        u.xhr.addEventListener('error', function () {
                            u.message.innerHTML = 'An error occured...';
                        }, false);
                        u.xhr.addEventListener('abort', function () {
                            u.message.innerHTML = 'Aborted...';
                        }, false);
                        u.xhr.open('POST', 'upload', true);
                        u.loaded = 0;
                        u.start = u.now = Date.now();
                        u.xhr.send(u.fd);
                    } else {
                        u.message.innerHTML = 'No file selected.';
                    }
                }, false);
                u.message.innerHTML = 'Ready.';
            };
            if (
                window.addEventListener  &&  window.removeEventListener  &&
                XMLHttpRequest  &&  XMLHttpRequestUpload  &&  FormData  &&
                Date  &&  Date.now  &&  File  && 
                document.querySelector  &&  document.createElement
            ) {
                window.addEventListener('load', u.init, false);
            }
        }({}));"""
    )


    @staticmethod
    def html (head=common_head, body=""):
        """Simple full-page HTML generator."""
        return (
            dedent("""\
                <!DOCTYPE html>
                <html dir="ltr" lang="en-US">
                    <head>
            """) + \
            indent(head, Template.indent*2) + \
            indent(dedent("""\
                    </head>
                    <body>
                        <h2><div class="logo">&nbsp;</div>pyfup</h2>
            """), Template.indent) + \
            indent(body, Template.indent*2) + \
            dedent("""\
                    </body>
                </html>"""
            )
        )




# FieldStorage class subclassed for override the default choice
# of storing all files in a temporary directory.
class FUPFieldStorage(FieldStorage):

    """multipart/form-data request body parser"""

    def __init__ (self, *args, **kwargs):
        """call parent constructor and store reference to the environ"""
        if "environ" in kwargs:
            self.__orig_env = kwargs["environ"]
        elif len(args) >= 3:
            self.__orig_env = args[3]
        else:
            self.__orig_env = {}
        # unfortunately in python 2.x FieldStorage is an old-style class
        # and thus super() call can't be used
        FieldStorage.__init__(self, *args, **kwargs)


    def make_file (self, binary=None):
        """create secure tempfile in the current directory"""
        self.secure_filename = ntbasename(posixbasename(self.filename))
        self.temp_filename = self.secure_filename + ".part"
        while os.path.exists(self.temp_filename):
            self.secure_filename += ".dup"
            self.temp_filename = self.secure_filename + ".part"
        print(
            "%s - - [%s] --> receiving \"%s\" (%s) %s" % (
                self.__orig_env["REMOTE_ADDR"] \
                    if "REMOTE_ADDR" in self.__orig_env else "-",
                time.strftime("%d/%b/%Y %H:%M:%S"),
                self.secure_filename,
                self.headers["content-type"],
                self.__orig_env["CONTENT_LENGTH"] \
                    if "CONTENT_LENGTH" in self.__orig_env else ""
            ),
            file=sys.stderr
        )
        return open(self.temp_filename, "wb+", buffering=1<<16)




# Define views with logic for all required functionality.
class View(object):

    """Views/actions for each URL defined in the application."""

    @staticmethod
    def index (env, config):
        """File upload page with an appropriate html form."""
        markup = dedent("""\
            <form
                action="upload"
                method="post"
                enctype="multipart/form-data"
            >
                <fieldset>
                    <input type="file" name="file" class="fselect">
                    <input type="submit" value="Upload File">
                </fieldset>
            </form>
            <div class="progressFrame"></div>
            <div class="message">
                Static uploading (no dynamic progress updates).
            </div>
        """)
        markup += dedent("""\
            <script
                type="text/javascript"
                charset="utf-8"
                src="m.js"
            >
            </script>
        """) if not config["no_js"] else ""
        return (
            "200 OK", [
                ("Content-Type", "text/html; charset=utf-8")
            ], utf8_encode(Template.html(body=markup))
        )


    @staticmethod
    def template (name, content_type, binary=False):
        """Returns static template text."""
        if binary:
            def enc (s):
                return s
        else:
            def enc (s):
                return utf8_encode(s)
        def t (env, config={}):
            return (
                "200 OK", [
                    ("Content-Type", content_type)
                ], enc(getattr(Template, name))
            )
        return t


    @staticmethod
    def upload (env, config={}):
        """File upload action (called from an upload form)."""
        form = FUPFieldStorage(fp=env["wsgi.input"], environ=env)
        form_file = form["file"] if "file" in form else None

        if form_file != None and form_file.filename:
            form_file.file.close()

            fn = form_file.secure_filename
            while os.path.exists(fn):
                fn += ".dup"
            os.rename(form_file.temp_filename, fn)

            status = "201 Created"
            message = \
                "The file \"%s\" was uploaded successfully!" \
                    % form_file.filename
            bytes_read = os.stat(fn).st_size

        else:
            status = "200 OK"
            message = "No file was uploaded."
            bytes_read = 0

        return (
            status, [
                ("Content-Type", "text/html; charset=utf-8")
            ], utf8_encode(Template.html(body=dedent("""\
                <p>Done!</p>
                <p>%s</p>
                <p>bytes uploaded: %u</p>
                <p>(<a href="..">upload another file</a>)</p>
            """ % (message, bytes_read))))
        )




# Create url -> view mapping,
# dispatch requests to appropriate views,
# optionally compress response
# and compute Content-Length.
class Application(object):

    """Base class for a web application."""

    def __init__ (self, config={}):
        """"url routing" and application config setup"""
        self.urls = {
            "/" : View.index,
            "/favicon.ico" : View.template(
                "favicon", "image/x-icon", True
            ),
            "/m.css" : View.template(
                "css", "text/css"
            ),
            "/m.js" : View.template(
                "client_logic", "application/javascript"
            ),
            "/upload" : View.upload
        }
        self.config = {
            "no_js" : False,
            "auth" : "__NO_AUTH__"
        }
        self.config.update(config)


    def authorized (self, env):
        """check if user agent authorized itself properly"""
        try:
            return (
                self.config["auth"] == "__NO_AUTH__" or (
                    "HTTP_AUTHORIZATION" in env and (
                        env["HTTP_AUTHORIZATION"].startswith("Basic ") and (
                            base64.b64decode(
                                env["HTTP_AUTHORIZATION"].split(" ")[1]
                            ) == utf8_encode(self.config["auth"])
                        )
                    )
                )
            )
        except:
            return False


    def dispatch (self, env):
        """Basic, url-based action dispatcher."""
        if env["PATH_INFO"] in self.urls:
            if self.authorized(env):
                return self.urls[env["PATH_INFO"]](env, self.config)
            else:
                return (
                    "401 Not Authorized", [
                        ("Content-Type", "text/plain; charset=utf-8"),
                        (
                            "WWW-Authenticate",
                            "Basic realm=\"pyfup v%s\"" % __version__
                        )
                    ], utf8_encode("Not Authorized")
                )
        else:
            return (
                "404 Not Found", [
                    ("Content-Type", "text/plain; charset=utf-8")
                ], utf8_encode(
                    "No action for \"%s\" route defined." \
                        % env["PATH_INFO"]
                )
            )


    def __call__ (self, env, start_response):
        """A callable defined for a WSGI entry point."""
        status, headers, body = self.dispatch(env)
        if (
            "HTTP_ACCEPT_ENCODING" in env and
            env["HTTP_ACCEPT_ENCODING"].find("gzip") > -1
        ):
            body = GzipGlue.compress(body)
            headers.append(
                ("Content-Encoding", "gzip")
            )
        headers.append(
            ("Content-Length", str(len(body)))
        )
        start_response(status, headers)
        return iter([body])




# WSGIRequestHandler class subclassed to log eventually occuring
# SSL socket exceptions in a nice one-liner without long traceback
class FUPRequestHandler(WSGIRequestHandler):

    """WSGI protocol."""

    def handle (self):
        """default request handler"""
        # python 2.x and 3.x compatible try-except code
        try:
            WSGIRequestHandler.handle(self)
        except:
            e = sys.exc_info()
            print(
                "%s - - [%s] request error: %s \"%s\"" % (
                    self.client_address[0],
                    time.strftime("%d/%b/%Y %H:%M:%S"),
                    e[0],
                    utf8_encode(e[1].reason, e="replace") \
                        if hasattr(e[1], "reason") \
                        else utf8_encode(e[1].strerror, e="replace")
                ),
                file=sys.stderr
            )


    def log_message (self, format, *args):
        """used by all default logging functions"""
        def simple_ascii (s, aux=(lambda x: x)):
            """ord 32 - 126 check"""
            answer = True
            for c in s:
                if not (aux(c) >= 32 and aux(c) <= 126):
                    answer = False
                    break
            return answer
        safe_args = []
        for a in args:
            if isinstance(a, int):
                safe_args.append(a)
            else:
                if (
                    isinstance(a, str) and simple_ascii(a, ord) or
                    not isinstance(a, str) and simple_ascii(a)
                ):
                        safe_args.append(a)
                else:
                    safe_args.append(
                        "unexpected content (base64): " + codecs.decode(
                            base64.b64encode(utf8_encode(a, e="replace")),
                            "utf-8"
                        )
                    )
        print(
            "%s - - [%s] %s" % (
                self.address_string(),
                self.log_date_time_string(),
                format % tuple(safe_args)
            ),
            file=sys.stderr
        )


    def log_error (self, format, *args):
        """log an error"""
        self.log_message(re.sub("(%.)", "\"\\1\"", format), *args)




# Parse command-line arguments,
# instantiate Application object
# and run WSGI server.
class Main(object):

    """Main program class."""

    def __init__ (self):
        """Program entry point."""
        args = self.parse_args()
        signal.signal(signal.SIGINT, self.exit)
        print(
            "[%s] -- exit: ctrl+C" % software_version,
            file=sys.stderr
        )

        if args.ssl:
            if not os.path.isfile(args.key):
                print(
                    "Provide a valid path to SSL key file " + \
                    "using --key argument.",
                    file=sys.stderr
                )
                self.exit()
            if not os.path.isfile(args.cert):
                print(
                    "Provide a valid path to SSL certificate " + \
                    "file using --cert argument.",
                    file=sys.stderr
                )
                self.exit()
        elif os.path.isfile(args.key) or os.path.isfile(args.cert):
            print("Use --ssl switch.", file=sys.stderr)
            self.exit()

        self.server_process = Process(
            target=self.run_server,
            args=(args.host, args.port, {
                "no_js" : args.no_js,
                "auth" : args.auth,
                "ppid" : os.getpid(),
                "ssl" : args.ssl,
                "key" : args.key,
                "cert" : args.cert
            })
        )
        self.server_process.start()
        self.main_loop()


    def parse_args (self):
        """Command-line argument parser."""
        try:
            from argparse import ArgumentParser
            argparser = ArgumentParser(
                description="Basic file upload WSGI application.",
                epilog="More at: https://github.com/drmats/pyfup"
            )
            argparser.add_argument(
                "-v", "--version", action="version",
                version="%(prog)s " + __version__
            )
            argparser.add_argument(
                "--ssl", action="store_true", default=False,
                help="use SSL"
            )
            argparser.add_argument(
                "-k", "--key", action="store", default="__NO_KEY__",
                type=str, help="path to SSL key file"
            )
            argparser.add_argument(
                "-c", "--cert", action="store", default="__NO_CERT__",
                type=str, help="path to SSL certificate file"
            )
            argparser.add_argument(
                "-a", "--auth", action="store", default="__NO_AUTH__",
                type=str, help=dedent("""\
                    specify username:password that will be required \
                    from user agent [default: no authentication required]"""
                )
            )
            argparser.add_argument(
                "--no-js", action="store_true", default=False,
                help="do not use JavaScript on client side"
            )
            argparser.add_argument(
                "--host", action="store", default="0.0.0.0",
                type=str, help="specify host [default: 0.0.0.0]"
            )
            argparser.add_argument(
                "port", action="store", default=8000, type=int,
                nargs="?", help="specify alternate port [default: 8000]"
            )
            return argparser.parse_args()
        except ImportError:
            class ArgsStub:
                host = "0.0.0.0"
                port = 8000
                no_js = False
                auth = "__NO_AUTH__"
                ssl = False
                key = "__NO_KEY__"
                cert = "__NO_CERT__"
            return ArgsStub()


    def exit (self, sig_num=None, stack_frame=None):
        """SIGINT/KeyboardInterrupt handler."""
        if hasattr(self, "server_process"):
            self.server_process.terminate()
        print("\nBye!", file=sys.stderr)
        sys.exit()


    def run_server (self, host, port, config):
        """WSGIServer config and main loop."""
        httpd = make_server(
            host, port, Application(config),
            handler_class=FUPRequestHandler
        )
        if config["ssl"]:
            try:
                import ssl
                httpd.socket = \
                    ssl.wrap_socket(
                        httpd.socket,
                        keyfile=config["key"],
                        certfile=config["cert"],
                        cert_reqs=ssl.CERT_NONE,
                        server_side=True
                    )
            except ImportError:
                print(
                    "SSL is not supported on this system.",
                    file=sys.stderr
                )
                os.kill(config["ppid"], signal.SIGINT)
                return
            except:
                e = sys.exc_info()
                print(
                    "Error: %s - \"%s\"." % (e[0], e[1].strerror),
                    file=sys.stderr
                )
                os.kill(config["ppid"], signal.SIGINT)
                return
        print(
            "listening on %s:%u%s"  % (
                host, httpd.server_port,
                " (SSL enabled)" if config["ssl"] else ""
            ),
            file=sys.stderr
        )
        httpd.serve_forever()


    def main_loop (self):
        """Main process loop (just to keep it alive)."""
        try:
            while True:
                input()
        except EOFError:
            self.exit()




# ...
if __name__ == "__main__":
    from multiprocessing import Process
    Main()
elif __name__ != "__parents_main__":
    app = Application()
