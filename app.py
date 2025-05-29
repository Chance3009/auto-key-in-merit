from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from datetime import datetime

app = Flask(__name__, static_url_path='/static')

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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    global progress
    progress = 0

    url = request.form["url"]
    file = request.files["file"]
    column = request.form.get("column", "MATRIC")

    df = pd.read_excel(file)
    if column not in df.columns:
        return f"Error: Column '{column}' not found."

    matric_numbers = df[column].dropna().astype(
        str).str.strip().drop_duplicates().tolist()
    results = process_data(url, matric_numbers)
    history_entry = update_history(len(matric_numbers), results)

    return jsonify({
        "status": "success",
        "message": "Process started!",
        "results": results,
        "history": history  # Send current history with response
    })


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
