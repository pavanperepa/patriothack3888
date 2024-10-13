from flask import Flask, jsonify, render_template, request
import requests
import cv2
import os
import random
import smtplib

app = Flask(__name__)

# Azure Custom Vision details
PREDICTION_KEY = ""
ENDPOINT = ""

OUTPUT_FOLDER = "frames_output"
FRAME_INTERVAL = 30

# Email credentials
SENDER_EMAIL = "irukasensei887@gmail.com"
APP_PASSWORD = ""

# Cleaners List (including email)
CLEANERS = [
    {"name": "John", "email": "irukasensei887@gmail.com"},
    {"name": "Jane", "email": "irukasensei887@gmail.com"},
    {"name": "Sam", "email": "irukasensei887@gmail.com"},
    {"name": "Emily", "email": "irukasensei887@gmail.com"},
    {"name": "Michael", "email": "irukasensei887@gmail.com"}
]

# Track already assigned cleaners
assigned_cleaners = []

@app.route('/')
def index():
    return render_template('index.html')

# Route to detect objects
@app.route('/detect', methods=['POST'])
def detect():
    result = capture_and_predict(OUTPUT_FOLDER, FRAME_INTERVAL, ENDPOINT, PREDICTION_KEY)
    return jsonify(result)

# Route to get available cleaners (excluding already assigned cleaners)
@app.route('/available-cleaners', methods=['GET'])
def available_cleaners():
    available = [cleaner for cleaner in CLEANERS if cleaner['name'] not in assigned_cleaners]
    return jsonify({"cleaners": available})

# Route to assign task to a cleaner
@app.route('/assign-task', methods=['POST'])
def assign_task():
    data = request.json
    task = data['task']
    cleaner_name = data['cleaner']

    # Find the cleaner details by name
    cleaner = next((c for c in CLEANERS if c['name'] == cleaner_name), None)
    if cleaner:
        # Add cleaner to assigned list
        assigned_cleaners.append(cleaner_name)
        # Send email to the assigned cleaner
        send_email_to_cleaner(cleaner, task)
        return jsonify({"message": f"Task '{task}' assigned to {cleaner['name']} and email sent."})
    return jsonify({"message": "Cleaner not found."})

# Function to send an email to the assigned cleaner
def send_email_to_cleaner(cleaner, task):
    subject = f"Task Assignment: {task.capitalize()}"
    message = f"Hello {cleaner['name']},\n\nA {task} has been detected in the building. Please address it at your earliest convenience.\n\nBest regards,\nBuilding Management"
    email_text = f"Subject: {subject}\n\n{message}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, cleaner['email'], email_text)
        server.quit()
        print(f"Email sent to {cleaner['email']}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to capture frames and detect objects
def capture_and_predict(output_folder, frame_interval, endpoint, prediction_key):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return {"message": "Error: Could not access the camera."}

    count = 0
    success, frame = cap.read()
    detected_objects = []

    while success:
        if count % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame{count}.jpg")
            cv2.imwrite(frame_path, frame)
            result = predict_image(frame_path, prediction_key, endpoint)
            detected_objects = check_for_objects(result)
            if detected_objects:
                cap.release()
                return {"message": "Objects detected.", "objects": detected_objects}
        success, frame = cap.read()
        count += 1

    cap.release()
    return {"message": "No objects detected."}

# Function to send frame to Azure Custom Vision and get the prediction result
def predict_image(frame_path, prediction_key, endpoint):
    headers = {'Prediction-Key': prediction_key, 'Content-Type': 'application/octet-stream'}
    with open(frame_path, 'rb') as image_file:
        image_data = image_file.read()
    url = f"{endpoint}/detect/iterations/Iteration3/image"
    try:
        response = requests.post(url, headers=headers, data=image_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during prediction request: {e}")
        return {}

# Function to check for objects
def check_for_objects(prediction_result):
    objects_to_detect = ['wallet', 'spill', 'drink', 'trash']
    detected_objects = []

    if 'predictions' not in prediction_result:
        print("Error: 'predictions' not found in the API response")
        return detected_objects

    for prediction in prediction_result['predictions']:
        if prediction['tagName'] in objects_to_detect and prediction['probability'] > 0.9:
            detected_objects.append(prediction['tagName'])

    return detected_objects

if __name__ == '__main__':
    app.run(debug=True)
