from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import requests
from datetime import datetime
import logging
import traceback
import os
import sys
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO since DEBUG is too verbose
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Only log to console in production
    ]
)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

progress = 0
total_count = 0
history = []  # Store history in memory


def create_error_response(error, status_code):
    """Helper function to create error responses"""
    logger.error(f"Error: {error}\n{traceback.format_exc()}")
    response = jsonify({
        "error": error.__class__.__name__,
        "details": str(error) if app.debug else "An unexpected error occurred"
    })
    response.headers['Content-Type'] = 'application/json'
    return response, status_code


@app.errorhandler(500)
def internal_error(error):
    return create_error_response(error, 500)


@app.errorhandler(404)
def not_found_error(error):
    return create_error_response(error, 404)


@app.errorhandler(400)
def bad_request_error(error):
    return create_error_response(error, 400)


@app.errorhandler(Exception)
def handle_exception(error):
    return create_error_response(error, 500)


def process_data(url, matric_numbers):
    global progress, total_count
    progress = 0
    total_count = len(matric_numbers)
    results = []
    session = requests.Session()

    # Process in batches of 10
    batch_size = 10
    for i in range(0, len(matric_numbers), batch_size):
        batch = matric_numbers[i:i + batch_size]
        batch_results = []

        for matric in batch:
            try:
                # First get the page to get any necessary cookies/tokens
                try:
                    initial_response = session.get(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.9",
                            "Connection": "keep-alive",
                        },
                        timeout=10
                    )
                    initial_response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to get initial page: {str(e)}")
                    raise

                # Prepare the form data
                payload = {
                    "user": matric.strip(),  # Ensure no whitespace
                    "login": "Login",
                    "submit": "Submit"
                }

                # Add additional headers that might be required
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": url.split('/')[0] + '//' + url.split('/')[2],
                    "Referer": url,
                    "Connection": "keep-alive",
                }

                # Submit the form
                response = session.post(
                    url,
                    data=payload,
                    headers=headers,
                    timeout=10,  # Increased timeout
                    allow_redirects=True  # Follow redirects
                )

                # Log response details for debugging
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                # First 500 chars
                logger.debug(f"Response content: {response.text[:500]}...")

                # Check if the response indicates success
                success = response.status_code == 200 and "error" not in response.text.lower()

                batch_results.append({
                    "matric": matric,
                    "status": "success" if success else "failed",
                    "timestamp": datetime.now().isoformat()
                })

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for matric {matric}")
                batch_results.append({
                    "matric": matric,
                    "status": "error",
                    "error": "Request timed out",
                    "timestamp": datetime.now().isoformat()
                })
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error for {matric}: {str(e)}")
                batch_results.append({
                    "matric": matric,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Unexpected error for {matric}: {str(e)}")
                batch_results.append({
                    "matric": matric,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

            # Update progress after each request
            progress = (len(results) + len(batch_results)) / total_count * 100

        # Add batch results to main results
        results.extend(batch_results)

        # Log batch completion
        logger.info(
            f"Completed batch {i//batch_size + 1} of {(len(matric_numbers) + batch_size - 1)//batch_size}")

    return results


def update_history(count, results):
    global history
    today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    entry = {
        "date": today,
        "count": count,
        "success_count": len([r for r in results if r["status"] == "success"]),
        "error_count": len([r for r in results if r["status"] == "error"]),
        "failed_count": len([r for r in results if r["status"] == "failed"])
    }

    history.insert(0, entry)
    history = history[:5]  # Keep only last 5 entries
    return entry


def read_excel_file(file):
    """Try different methods to read the Excel file."""
    try:
        # Try reading with default engine
        return pd.read_excel(file)
    except Exception as e1:
        logger.warning(f"Failed to read with default engine: {str(e1)}")
        try:
            # Try with openpyxl engine
            return pd.read_excel(file, engine='openpyxl')
        except Exception as e2:
            logger.warning(f"Failed to read with openpyxl: {str(e2)}")
            try:
                # Try with xlrd engine for older .xls files
                return pd.read_excel(file, engine='xlrd')
            except Exception as e3:
                logger.error(f"All Excel reading attempts failed: {str(e3)}")
                raise Exception(
                    "Unable to read the Excel file. Please ensure it's a valid .xlsx or .xls file.")


@app.route("/")
def home():
    try:
        logger.info("Serving home page")
        # Ensure the template exists
        if not os.path.exists(os.path.join(app.template_folder, 'index.html')):
            logger.error("index.html template not found")
            return "Template not found", 500

        return render_template("index.html")
    except Exception as e:
        logger.error(
            f"Error serving home page: {str(e)}\n{traceback.format_exc()}")
        return "Internal Server Error", 500


@app.route("/process", methods=["POST"])
def process():
    global progress, total_count
    progress = 0

    try:
        logger.info("Received /process request")
        logger.debug(f"Form data: {request.form}")
        logger.debug(f"Files: {request.files}")

        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename:
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400

        if 'url' not in request.form:
            logger.error("No URL provided")
            return jsonify({"error": "URL is required"}), 400

        url = request.form["url"].strip()
        column = request.form.get("column", "MATRIC")

        logger.info(
            f"Processing request - URL: {url}, File: {file.filename}, Column: {column}")

        # Validate URL
        if not url.startswith(('http://', 'https://')):
            logger.error("Invalid URL format")
            return jsonify({"error": "Invalid URL format. URL must start with http:// or https://"}), 400

        # Test URL accessibility
        try:
            test_response = requests.get(url, timeout=5)
            test_response.raise_for_status()
            logger.info(f"URL test successful: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"URL test failed: {str(e)}")
            return jsonify({"error": f"Could not access the provided URL: {str(e)}"}), 400

        # Save file temporarily for debugging
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(temp_path)
        logger.info(f"Saved file temporarily at: {temp_path}")

        try:
            df = pd.read_excel(temp_path)
            logger.info(
                f"Successfully read Excel file. Columns: {df.columns.tolist()}")
        except Exception as e:
            logger.error(
                f"Failed to read Excel file: {str(e)}\n{traceback.format_exc()}")
            return jsonify({"error": f"Failed to read Excel file: {str(e)}"}), 400

        if column not in df.columns:
            available_columns = df.columns.tolist()
            logger.error(
                f"Column '{column}' not found. Available columns: {available_columns}")
            return jsonify({
                "error": f"Column '{column}' not found. Available columns: {', '.join(available_columns)}"
            }), 400

        matric_numbers = df[column].dropna().astype(
            str).str.strip().drop_duplicates().tolist()
        logger.info(f"Found {len(matric_numbers)} matric numbers")

        if not matric_numbers:
            logger.error("No valid matric numbers found in the file")
            return jsonify({"error": "No valid matric numbers found in the selected column"}), 400

        # Log first few matric numbers for debugging
        logger.debug(f"First few matric numbers: {matric_numbers[:5]}")

        results = process_data(url, matric_numbers)
        history_entry = update_history(len(matric_numbers), results)

        response_data = {
            "status": "success",
            "message": "Process completed successfully",
            "results": results,
            "history": history
        }

        logger.info("Process completed successfully")
        return jsonify(response_data)

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(
            f"Unexpected error in process endpoint: {str(e)}\n{error_details}")
        return jsonify({
            "error": str(e),
            "details": error_details
        }), 500


@app.route("/progress")
def get_progress():
    try:
        return jsonify({
            "progress": progress,
            "current": int(progress * total_count / 100) if total_count > 0 else 0,
            "total": total_count
        })
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({
            "error": "Failed to get progress",
            "details": str(e)
        }), 500


@app.route("/history")
def get_history():
    return jsonify(history)


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
