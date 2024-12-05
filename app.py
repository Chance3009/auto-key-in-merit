from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import subprocess

app = Flask(__name__)

progress = 0


def process_data(url, matric_numbers):
    global progress
    progress = 0
    total = len(matric_numbers)

    # Configure Chrome options for headless mode
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # Initialize WebDriver
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)
    driver.get(url)

    try:
        # Loop through each matric number and process it
        for i, matric_number in enumerate(matric_numbers):
            input_field = driver.find_element(By.NAME, "user")
            input_field.send_keys(matric_number)
            driver.find_element(By.NAME, "login").click()

            # Simulate a time delay for each action and update progress
            time.sleep(1)

            # Update progress
            progress = (i + 1) / total * 100

        driver.quit()
    except Exception as e:
        driver.quit()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    global progress
    progress = 0  # Reset progress at the start

    # Get the form data (URL and Excel file)
    url = request.form["url"]
    file = request.files["file"]

    if not url or not file:
        return "Please provide the website link and an Excel file."

    df = pd.read_excel(file)
    if "MATRIC" not in df.columns:
        return "Error: Column 'MATRIC' not found. Please rename it."

    matric_numbers = df["MATRIC"].tolist()

    process_data(url, matric_numbers)

    return jsonify({"status": "success", "message": "Process started!"})


@app.route("/progress")
def get_progress():
    return jsonify({"progress": progress})


@app.route('/check-chrome')
def check_chrome():
    try:
        # Run the command to check Chrome version
        chrome_version = subprocess.check_output(
            ['google-chrome', '--version']).decode('utf-8')
        return f"Chrome is installed: {chrome_version}"
    except subprocess.CalledProcessError:
        return "Chrome is not installed."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
