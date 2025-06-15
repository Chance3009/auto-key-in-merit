import functions_framework
from app import app as flask_app


@functions_framework.http
def app(request):
    return flask_app(request.environ, lambda x, y: y)
