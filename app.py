from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)
progress = 0
total_count = 0  


def process_data(url, matric_numbers):
    global progress, total_count
    progress = 0
    total_count = len(matric_numbers)

    session = requests.Session()

    for i, matric in enumerate(matric_numbers):
        # Simulate the POST request
        payload = {
            "user": matric,
            "login": "Login"
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": url,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = session.post(url, data=payload, headers=headers)
            # You can parse HTML here to detect success/failure (optional)
        except Exception as e:
            print(f"Error on {matric}: {e}")

        progress = (i + 1) / total_count * 100


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

    matric_numbers = df[column].dropna().astype(str).str.strip().drop_duplicates().tolist()
    process_data(url, matric_numbers)

    return jsonify({"status": "success", "message": "Process started!"})


@app.route("/progress")
def get_progress():
    return jsonify({
        "progress": progress,
        "total": total_count,
        "current": int(progress * total_count / 100)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
