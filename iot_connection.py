import ssl
import os
import json
from azure.iot.device import IoTHubDeviceClient, Message
import cv2
import requests
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

# Disable SSL verification (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context

# Replace with your IoT Hub device connection string
CONNECTION_STRING = ""

# ThreadPoolExecutor to process predictions asynchronously
executor = ThreadPoolExecutor(max_workers=4)

def capture_from_camera_and_predict(output_folder, frame_interval, endpoint, prediction_key, device_client):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(0)  # Access the webcam
    count = 0
    success, frame = cap.read()
    
    while success:
        if count % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame{count}.jpg")
            cv2.imwrite(frame_path, frame)
            
            # Use the thread pool to handle prediction and message sending asynchronously
            executor.submit(predict_and_send_async, frame_path, prediction_key, endpoint, device_client)

        success, frame = cap.read()
        count += 1

    cap.release()
    cv2.destroyAllWindows()

def predict_and_send_async(frame_path, prediction_key, endpoint, device_client):
    result = predict_image(frame_path, prediction_key, endpoint)
    detected_objects = check_for_objects(result)
    
    if detected_objects:
        event_data = {
            "event_type": detected_objects,
            "timestamp": "2024-10-13T08:00:00Z",
            "location": "Room 101"
        }
        send_message_to_iot_hub(device_client, event_data)

def predict_image(frame_path, prediction_key, endpoint):
    headers = {
        'Prediction-Key': prediction_key,
        'Content-Type': 'application/octet-stream'
    }
    
    with open(frame_path, 'rb') as image_file:
        image_data = image_file.read()

    url = f"{endpoint}/detect/iterations/Iteration3/image"
    
    try:
        # Add timeout to the request to avoid indefinite blocking
        response = requests.post(url, headers=headers, data=image_data, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error while making prediction request: {e}")
        return {}

def check_for_objects(prediction_result):
    objects_to_detect = ['wallet', 'spill', 'drink', 'trash']
    detected_objects = []
    
    if 'predictions' not in prediction_result:
        print("Error: 'predictions' not found in the API response")
        return detected_objects

    for prediction in prediction_result['predictions']:
        if prediction['tagName'] in objects_to_detect and prediction['probability'] > 0.5:
            detected_objects.append(prediction['tagName'])
    
    return detected_objects

def send_message_to_iot_hub(device_client, event_data):
    try:
        # Convert event data to JSON format
        message = Message(json.dumps(event_data))
        message.content_encoding = "utf-8"
        message.content_type = "application/json"
        print(f"Sending message to IoT Hub: {event_data}")
        device_client.send_message(message)
    except Exception as e:
        print(f"Failed to send message to IoT Hub: {e}")

def main():
    # Create an IoT Hub client
    device_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    
    try:
        # Connect the device to IoT Hub
        print("Connecting to IoT Hub...")
        device_client.connect()
        print("Device successfully connected to IoT Hub!")
        
        # Example usage of capturing and predicting with IoT Hub communication
        output_folder = "frames_output"
        frame_interval = 30  # Process every 30th frame
        endpoint = ""
        prediction_key = ""
        
        capture_from_camera_and_predict(output_folder, frame_interval, endpoint, prediction_key, device_client)
    
    except KeyboardInterrupt:
        print("Process interrupted.")
    
    finally:
        # Gracefully shut down the ThreadPoolExecutor
        print("Waiting for all tasks to complete...")
        executor.shutdown(wait=True)  # Wait for all threads to finish
        print("All tasks completed. Shutting down.")
        
        # Disconnect the device
        print("Disconnecting from IoT Hub...")
        device_client.disconnect()
        print("Device disconnected.")

if _name_ == "_main_":
    main()