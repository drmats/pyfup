#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Basic file upload WSGI application (python 2.x/3.x).

This script brings up a simple_server from python's wsgiref
package and runs a really simple web application on it.
It allows to upload any file using multipart/form-data encoding.
Don't use it in production environment as it has not been
reviewed for security issues, however it's handy for ad-hoc
file transfers between machines over HTTP protocol.
"""

from __future__ import print_function, absolute_import
import sys, os, signal, argparse, cgi, base64, gzip
from wsgiref.simple_server import make_server

__author__ = "drmats"
__version__ = "0.2.6"
__license__ = "BSD 2-Clause license"




# ...
class GzipGlue:

    """Gzip glue compat. layer for compress/decompress functions."""

    # emulates gzip.compress from python >=3.2
    @staticmethod
    def _compress_p2 (s):
        osio = StringIO()
        try:
            with gzip.GzipFile(fileobj=osio, mode="wb") as g:
                g.write(s)
            return osio.getvalue()
        finally:
            osio.close()


    # emulates gzip.decompress from python >=3.2
    @staticmethod
    def _decompress_p2 (s):
        isio = StringIO(s)
        try:
            with gzip.GzipFile(fileobj=isio, mode="rb") as g:
                return g.read()
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
        return "\n".join(map(
            lambda l: i+l if l!="" else l,
            s.split("\n")
        ))




# ...
class Markup:

    """Markup definitions."""

    # default indent
    indent = " "*4


    # common html head
    common_head = dedent("""\
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=Edge">
        <meta http-equiv="content-style-type" content="text/css">
        <link rel="icon" type="image/x-icon" href="favicon.ico">
        <title>pyfup</title>
        <link rel="stylesheet" type="text/css" href="m.css" media="screen">
    """)


    # ...
    css = dedent("""\
        @charset "utf-8";
        html {
            font-size: 14px;
            font-family: monospace;
            padding: 16px;
            line-height: 28px;
        }
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
            background-repeat: none;
            background-position: center center;
        }
        a, a:visited { text-decoration: none; color: blue; }
        a:hover { text-decoration: underline; }
        p { margin: 0px; padding: 0px; }\
    """)


    # ...
    favicon = dedent("""\
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
        6hdeyLdfe3X4j+uoj+OIm+Ks9Ois0fhfJ6j1zUrM6JngCTkE5/fgQAAA==\
    """)


    # ...
    @staticmethod
    def html (head=common_head, body=""):
        return (
            dedent("""\
                <!DOCTYPE html>
                <html dir="ltr" lang="en-US">
                    <head>
            """) + \
            indent(head, Markup.indent*2) + \
            indent(dedent("""\
                    </head>
                    <body>
                        <h2><div class="logo">&nbsp;</div>pyfup</h2>
            """), Markup.indent) + \
            indent(body, Markup.indent*2) + \
            dedent("""\
                    </body>
                </html>\
            """)
        )




# ...
class View:

    """Views/actions for each URL defined in the application."""

    # file upload page with an appropriate html form
    @staticmethod
    def index (env):
        return (
            "200 OK", [
                ("Content-Type", "text/html; charset=utf-8")
            ], Markup.html(body=dedent("""\
                <form
                    action="upload"
                    method="post"
                    enctype="multipart/form-data"
                >
                    <input type="file" name="file"><br>
                    <input type="submit" value="Upload File">
                </form>
            """)).encode("utf-8")
        )


    # ...
    @staticmethod
    def favicon (env):
        return (
            "200 OK", [
                ("Content-Type", "image/x-icon")
            ], GzipGlue.decompress(base64.b64decode(
                Markup.favicon.encode("utf-8")
            ))
        )


    # ...
    @staticmethod
    def css (env):
        return (
            "200 OK", [
                ("Content-Type", "text/css")
            ], Markup.css.encode("utf-8")
        )


    # file upload action (called from an upload form)
    @staticmethod
    def upload (env):
        def megbuffer (f):
           while True:
              chunk = f.read(1024**2)
              if not chunk: break
              yield chunk

        form = cgi.FieldStorage(
            fp=env["wsgi.input"], environ=env
        )

        form_file = form["file"] if "file" in form else None

        if form_file != None and form_file.filename:
            fn = os.path.basename(form_file.filename)
            with open(fn, "wb", buffering=0) as out:
                for chunk in megbuffer(form_file.file):
                    out.write(chunk)
                message = \
                    "The file \"" + fn + "\" " + \
                    "was uploaded successfully!"
                bytes_read = out.tell()
        else:
            message = "No file was uploaded."
            bytes_read = 0

        return (
            "200 OK", [
                ("Content-Type", "text/html; charset=utf-8")
            ], Markup.html(body=dedent("""\
                <p>Done!</p>
                <p>%s</p>
                <p>bytes uploaded: %u</p>
                <p>(<a href="..">upload another file</a>)</p>
            """ % (message, bytes_read))).encode("utf-8")
        )




# ...
class Application:

    """Base class for a web application."""

    # "url routing" setup
    def __init__ (self):
        self.urls = {
            "/" : View.index,
            "/favicon.ico" : View.favicon,
            "/m.css" : View.css,            
            "/upload" : View.upload
        }


    # basic, url-based action dispatcher
    def dispatch (self, env):
        if env["PATH_INFO"] in self.urls:
            return self.urls[env["PATH_INFO"]](env)
        else:
            return (
                "404 Not Found", [
                    ("Content-Type", "text/plain; charset=utf-8")
                ], (
                    "No action for \"%s\" route defined."
                        % env["PATH_INFO"]
                ).encode("utf-8")
            )


    # a callable defined for a WSGI entry point
    def __call__ (self, env, start_response):
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
        return [body]




# ...
class Main:

    """Main program class."""

    # ...
    def __init__ (self):
        args = self.parse_args()
        signal.signal(
            signal.SIGINT,
            Main.exit_handler
        )
        print("Hi there! (*:%u)" % args.port)
        make_server(
            "", args.port,
            Application()
        ).serve_forever()


    # command-line argument parser
    def parse_args (self):
        argparser = argparse.ArgumentParser(
            description="Basic file upload WSGI application.",
            epilog="More at: https://github.com/drmats/pyfup"
        )
        argparser.add_argument(
            "port", action="store", default=8000, type=int,
            nargs="?", help="Specify alternate port [default: 8000]"
        )
        argparser.add_argument(
            "-v", "--version", action="version",
            version="%(prog)s " + __version__
        )
        return argparser.parse_args()


    # SIGINT/KeyboardInterrupt handler
    @staticmethod
    def exit_handler (sig_num, stack_frame):
        print("\nBye!")
        sys.exit()




# ...
if __name__ == "__main__":
    Main()
