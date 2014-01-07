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
import sys, os, signal
import textwrap, argparse, cgi, gzip
from wsgiref.simple_server import make_server

__author__ = "drmats"
__version__ = "0.2.3"
__license__ = "BSD 2-Clause license"




# ...
class GzipGlue:

    """Gzip glue layer for compress/decompress functions."""

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


# based on simple "feature detection" assign compress/decompress methods
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




# ...
class Markup:

    """"Static" text markup definitions."""

    # simple html upload form
    simple_upload = textwrap.dedent("""\
        <!DOCTYPE html>
        <html dir="ltr" lang="en-US">
        <head>
            <meta charset="utf-8">
            <meta http-equiv="X-UA-Compatible" content="IE=Edge">
            <meta http-equiv="content-style-type" content="text/css">
            <title>File Upload</title>
            <style media="screen">
                html {
                    font-size: 14px;
                    font-family: monospace;
                    padding: 10px;
                    line-height: 28px;
                }
            </style>
        </head>
        <body>
            Upload a file:
            <form
                action="upload/"
                method="post"
                enctype="multipart/form-data"
            >
                <input type="file" name="file"><br>
                <input type="submit" value="Upload File">
            </form>
            (<a href="info/">env. info</a>)
        </body>
        </html>\
    """)




# ...
class View:

    """Views/actions for each URL defined in the application."""

    # file upload page with an appropriate html form
    @staticmethod
    def index (env):
        return (
            "200 OK", [
                ("Content-Type", "text/html; charset=utf-8")
            ], Markup.simple_upload.encode("utf-8")
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
            out = open(fn, "wb", buffering=0)
            for chunk in megbuffer(form_file.file):
                out.write(chunk)
            message = \
                "The file \"" + fn + "\" " + \
                "was uploaded successfully!"
            bytes_read = out.tell()
            out.close()
        else:
            message = "No file was uploaded."
            bytes_read = 0

        return (
            "200 OK", [
                ("Content-Type", "text/plain; charset=utf-8")
            ], (
                "Done!\n\n%s\n\nStatus:\nbytes read: %u"
                    % (message, bytes_read)
            ).encode("utf-8")
        )


    # show current environment (key-val mapping)
    @staticmethod
    def info (env):
        resp = ["%s: %s" % (key, value)
            for key, value in sorted(env.items())
        ]
        resp = "\n".join(resp)
        return (
            "200 OK", [
                ("Content-Type", "text/plain; charset=utf-8")
            ], resp.encode("utf-8")
        )




# ...
class Application:

    """Base class for a web application."""

    # "url routing" setup
    def __init__ (self):
        self.urls = {
            "/" : View.index,
            "/upload/" : View.upload,
            "/info/" : View.info
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
        headers.append(
            ("Content-Length", str(sys.getsizeof(body)))
        )
        if (
            "HTTP_ACCEPT_ENCODING" in env and
            env["HTTP_ACCEPT_ENCODING"].find("gzip") > -1
        ):
            body = GzipGlue.compress(body)
            headers.append(
                ("Content-Encoding", "gzip")
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
