#!/usr/bin/env python

import os
import io
from flask import Flask, request, jsonify
from multiprocessing import Value


app = Flask(__name__)

# version and build string placed into env by Docker ENV
version_str = ""
buildtime_str = ""

# env keys set by k8s
k8s_downward_env_list = ["MY_NODE_NAME","MY_POD_NAME","MY_POD_IP","MY_POD_SERVICE_ACCOUNT"]

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
    print(upath)
    if not upath.startswith(app_context):
      return app.response_class("404 only configured to deliver from {}".format(app_context),status=404,mimetype="text/plain") 

    # increment request counter
    with counter.get_lock():
        requestcount = counter.value
        counter.value += 1

    # create buffered response
    buffer = io.StringIO()
    buffer.write( "{} {} {}\n".format(requestcount,request.method,request.path) )
    buffer.write( "path: {}\n".format(request.path) )
    buffer.write( "Host: {}\n".format(request.headers.get('Host') ))

    # check for env values from downward API
    for keyname in k8s_downward_env_list:
        buffer.write ( "{} = {}\n".format(keyname, os.getenv(keyname,"none")) )

    return app.response_class(buffer.getvalue(), status=200, mimetype="text/plain")


@app.route("/healthz")
def health():
    """ kubernetes health endpoint """
    return jsonify(
        { 'health':'ok','Version':version_str, 'BuildTime':buildtime_str }
    )


if __name__ == '__main__' or __name__ == "main":

    debugVal = bool(os.getenv("DEBUG",False))
    # avoids error with jsonify that checks request.is_xhr
    # https://github.com/pallets/flask/issues/2549
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

    version_str = os.getenv("MY_VERSION","none")
    buildtime_str = os.getenv("MY_BUILDTIME","none")
    print("build version/time: {}/{}".format(version_str,buildtime_str))

    app_context = os.getenv("APP_CONTEXT","/")
    print("app context: {}".format(app_context))

    port = int(os.getenv("PORT", 8000))
    print("Starting web server on port {}".format(port))

    app.run(debug=debugVal, host='0.0.0.0', port=port)


