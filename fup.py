#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Basic file upload WSGI application (python 3.x).

This script brings up a simple_server from python's wsgiref
package and runs a really simple web application on it.
It allows to upload any file using multipart/form-data encoding.
Don't use it in production environment as it has not been
reviewed for security issues, however it's handy for ad-hoc
file transfers between machines over HTTP protocol.
"""

import sys, os, cgi
from wsgiref.simple_server import make_server

__author__ = "drmats"
__version__ = "0.1.0"
__license__ = "BSD 2-Clause license"




# ...
class View:

    """Views/actions for each URL defined in application."""

    # file upload page with appropriate html form
    def index (env):
        return (
            "200 OK",
            [("Content-Type", "text/html; charset=utf-8")],
            """\
<!DOCTYPE html>
<html>
<head>
    <title>File Upload</title>
    <style media="screen">
        html {
            font-size: 14px;
            font-family: monospace;
            padding: 40px;
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
</html>"""
        )


    # file upload action (called from upload form)
    def upload (env):
        chunk_size = 1024*1024

        def fbuffer (f):
           while True:
              chunk = f.read(chunk_size)
              if not chunk: break
              yield chunk

        form = cgi.FieldStorage(
            fp=env["wsgi.input"], environ=env
        )

        try:
            form_file = form["file"]
        except KeyError:
            form_file = None

        if form_file != None and form_file.filename:
            fn = os.path.basename(form_file.filename)
            out = open(fn, "wb", buffering=0)
            for chunk in fbuffer(form_file.file):
                out.write(chunk)
            out.close()
            message = \
                "The file \"" + fn + "\" " + \
                "was uploaded successfully!"
            bytes_read = str(form_file.bytes_read)
        else:
            message = "No file was uploaded."
            bytes_read = "0"

        return (
            "200 OK",
            [("Content-Type", "text/plain; charset=utf-8")],
            "Done!\n\n%s\n\nStatus:\nbytes read: %s"
                % (message, bytes_read)
        )


    # show key-val environment mapping
    def info (env):
        resp = ["%s: %s" % (key, value)
            for key, value in sorted(env.items())
        ]
        resp = "\n".join(resp)
        return (
            "200 OK",
            [("Content-Type", "text/plain; charset=utf-8")],
            resp
        )




# ...
class Application:

    """Base class for web application."""

    # "url routing" setup
    def __init__ (self):
        self.urls = {
            "/" : View.index,
            "/upload/" : View.upload,
            "/info/" : View.info
        }


    # basic action dispatcher (url-based)
    def dispatch (self, env):
        try:
            return self.urls[env["PATH_INFO"]](env)
        except KeyError:
            return (
                "404 Not Found",
                [("Content-Type", "text/plain; charset=utf-8")],
                "No action for \"%s\" route defined."
                    % env["PATH_INFO"]
            )


    # a callable defined for a WSGI entry point
    def __call__ (self, env, start_response):
        status, headers, body = self.dispatch(env)
        body = body.encode("utf-8")
        headers.append(("Content-Length", str(len(body))))
        start_response(status, headers)
        return [body]




# ...
if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
    except IndexError:
        port = 8000
    print("Hi there! (*:%s)" % str(port))
    make_server(
        "", port,
        Application()
    ).serve_forever()
