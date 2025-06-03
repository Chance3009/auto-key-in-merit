from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from datetime import datetime
import logging
import traceback
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

progress = 0
total_count = 0
history = []  # Store history in memory instead of file


def process_data(url, matric_numbers):
    global progress, total_count
    progress = 0
    total_count = len(matric_numbers)
    results = []
    session = requests.Session()

    for i, matric in enumerate(matric_numbers):
        try:
            # Simulate the POST request
            payload = {
                "user": matric.strip(),  # Ensure no whitespace
                "login": "Login"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": url,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }

            response = session.post(
                url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            # Add to results
            results.append({
                "matric": matric,
                "status": "success" if response.status_code == 200 else "failed",
                "timestamp": datetime.now().isoformat()
            })

        except requests.exceptions.RequestException as e:
            print(f"Network error for {matric}: {str(e)}")
            results.append({
                "matric": matric,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Unexpected error for {matric}: {str(e)}")
            results.append({
                "matric": matric,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        progress = (i + 1) / total_count * 100

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
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    global progress
    progress = 0

    try:
        # Validate request data
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if not file.filename:
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400

        # Check file extension
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            logger.error("Invalid file type")
            return jsonify({"error": "Please upload a valid Excel file (.xlsx or .xls)"}), 400

        if 'url' not in request.form:
            logger.error("No URL provided")
            return jsonify({"error": "URL is required"}), 400

        url = request.form["url"]
        column = request.form.get("column", "MATRIC")

        logger.info(
            f"Processing request - URL: {url}, File: {file.filename}, Column: {column}")

        try:
            df = read_excel_file(file)
        except Exception as e:
            logger.error(f"Failed to read Excel file: {str(e)}")
            return jsonify({"error": str(e)}), 400

        if df.empty:
            logger.error("Excel file is empty")
            return jsonify({"error": "The Excel file is empty"}), 400

        if column not in df.columns:
            available_columns = df.columns.tolist()
            logger.error(
                f"Column '{column}' not found. Available columns: {available_columns}")
            return jsonify({
                "error": f"Column '{column}' not found. Available columns: {', '.join(available_columns)}"
            }), 400

        matric_numbers = df[column].dropna().astype(
            str).str.strip().drop_duplicates().tolist()

        if not matric_numbers:
            logger.error("No valid matric numbers found in the file")
            return jsonify({"error": "No valid matric numbers found in the selected column"}), 400

        logger.info(f"Processing {len(matric_numbers)} matric numbers")

        results = process_data(url, matric_numbers)
        history_entry = update_history(len(matric_numbers), results)

        response_data = {
            "status": "success",
            "message": "Process completed successfully",
            "results": results,
            "history": history,
            "total_processed": len(matric_numbers),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "errors": len([r for r in results if r["status"] == "error"])
        }

        logger.info(f"Process completed: {response_data}")
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
    return jsonify({
        "progress": progress,
        "total": total_count,
        "current": int(progress * total_count / 100)
    })


@app.route("/history")
def get_history():
    return jsonify(history)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
