"""
WSGI entry for single-container deploy.
Mounts the Flask app under /supermarket so one public URL works:
  https://your-app.onrender.com/supermarket/
"""
import os

# Ensure relative paths (templates, uploads, config.json) resolve correctly
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response

from app import app as flask_app


def _not_found(environ, start_response):
    return Response("Not Found — try /supermarket/", status=404)(environ, start_response)


# Requests to /supermarket/* → Flask; everything else → 404 (nginx won't send them here)
application = DispatcherMiddleware(_not_found, {
    "/supermarket": flask_app,
})
