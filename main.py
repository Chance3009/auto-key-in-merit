import functions_framework
from app import app as flask_app


@functions_framework.http
def app(request):
    # Set the base URL for the Flask app
    request.environ['SCRIPT_NAME'] = ''
    return flask_app(request.environ, lambda x, y: y)
