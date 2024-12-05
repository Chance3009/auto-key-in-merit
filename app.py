from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    url = request.form["url"]
    file = request.files["file"]

    if not url or not file:
        return "Please provide the website link and an Excel file."

    df = pd.read_excel(file)
    if "MATRIC" not in df.columns:
        return "Error: Column 'MATRIC' not found. Please rename it."

    matric_numbers = df["MATRIC"].tolist()

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)

        for matric_number in matric_numbers:
            input_field = driver.find_element(By.NAME, "user")
            input_field.send_keys(matric_number)
            driver.find_element(By.NAME, "login").click()

        driver.quit()
        return "Process Completed Successfully!"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
