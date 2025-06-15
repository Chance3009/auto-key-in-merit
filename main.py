import functions_framework
from app import app as flask_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def app(request):
    try:
        logger.info(f"Received request for path: {request.path}")

        # Set the base URL for the Flask app
        request.environ['SCRIPT_NAME'] = ''

        # Ensure the path is properly handled
        if request.path == '/':
            request.environ['PATH_INFO'] = '/'
            logger.info("Handling root path request")

        # Log the request details
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")

        # Process the request through Flask
        response = flask_app(request.environ, lambda x, y: y)

        logger.info(f"Response status: {response.status}")
        return response

    except Exception as e:
        logger.error(f"Error in Firebase Function: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Internal Server Error'
        }, 500
