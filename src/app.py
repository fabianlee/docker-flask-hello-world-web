#!/usr/bin/env python
#
# simple flask application with synchronized global counter
#

import os
import io
import logging
from flask import Flask, request, jsonify
from multiprocessing import Value

# log level mutes every request going to stdout
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

# version and build string placed into env by Docker ENV
message_to = "World"

# global request counter
# https://stackoverflow.com/questions/42680357/increment-counter-for-every-access-to-a-flask-view
counter = Value('i', 0)

# https://riptutorial.com/flask/example/19420/catch-all-route
# catches both / and then all other
@app.route('/', defaults={'upath': ''})
@app.route("/<path:upath>")
def entry_point(upath):
    """ delivers HTTP response """

    # check for valid app_context
    upath = "/" + upath
    print("Request to {}".format(upath))
    if not upath.startswith(app_context):
      return app.response_class("404 only configured to deliver from {}".format(app_context),status=404,mimetype="text/plain") 

    # increment request counter
    with counter.get_lock():
        requestcount = counter.value
        counter.value += 1

    # create buffered response
    buffer = io.StringIO()
    buffer.write( "Hello, {}\n".format(message_to))
    buffer.write( "request {} {} {}\n".format(requestcount,request.method,request.path) )
    buffer.write( "Host: {}\n".format(request.headers.get('Host') ))

    return app.response_class(buffer.getvalue(), status=200, mimetype="text/plain")


@app.route("/healthz")
def health():
    """ kubernetes health endpoint """
    return jsonify(
        { 'health':'ok','Version':version_str, 'BuildTime':buildtime_str }
    )

if __name__ == '__main__' or __name__ == "main":

    # avoids error with jsonify that checks request.is_xhr
    # https://github.com/pallets/flask/issues/2549
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

    # read optional environment variables
    app_context = os.getenv("APP_CONTEXT","/")
    print("app context: {}".format(app_context))

    port = int(os.getenv("PORT", 8000))
    print("Starting web server on port {}".format(port))

    message_to = os.getenv("MESSAGE_TO","World")
    print("message_to: {}".format(message_to))

    app.run(debug=False, host='0.0.0.0', port=port)


