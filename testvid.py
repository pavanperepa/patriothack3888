import requests
import cv2
import os

# Function to capture live frames from the camera and predict wallet presence using the Custom Vision model
def capture_from_camera_and_predict(output_folder, frame_interval, endpoint, prediction_key):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cap = cv2.VideoCapture(0)  # Access the webcam
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    count = 0
    success, frame = cap.read()
    while success:
        if count % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame{count}.jpg")
            cv2.imwrite(frame_path, frame)
            
            # Send the frame to Custom Vision for prediction
            result = predict_image(frame_path, prediction_key, endpoint)
            
            # Check if a wallet is detected
            wallet_detected = check_for_wallet(result)
            if wallet_detected:
                # Highlight the frame if a wallet is detected
                cv2.putText(frame, "Wallet Detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                print(f"Wallet detected in frame {count}")
        
        # Display the frame (with wallet detection info if any)
        cv2.imshow("Live Camera Feed", frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        success, frame = cap.read()
        count += 1

    cap.release()
    cv2.destroyAllWindows()  # Close the camera and windows

# Function to send frame to Azure Custom Vision and get the prediction result
def predict_image(frame_path, prediction_key, endpoint):
    headers = {
        'Prediction-Key': prediction_key,
        'Content-Type': 'application/octet-stream'
    }

    with open(frame_path, 'rb') as image_file:
        image_data = image_file.read()

    url = f"{endpoint}/detect/iterations/Iteration3/image"
    response = requests.post(url, headers=headers, data=image_data)

    # Return the response in JSON format without printing the full response
    return response.json()


# Function to check if the 'wallet' class is predicted in the result
def check_for_wallet(prediction_result):
    # Add error handling for unexpected API responses
    if 'predictions' not in prediction_result:
        print("Error: 'predictions' not found in the API response")
        return False  # No wallet detected in case of error

    # Only check for wallet predictions with confidence above 50%
    for prediction in prediction_result['predictions']:
        if prediction['tagName'] == 'wallet' and prediction['probability'] > 0.5:
            return True
    return False


# Example usage
output_folder = "frames_output"  # Folder to store frames
frame_interval = 30  # Process every 30th frame
endpoint = ""  # Updated endpoint
prediction_key = ""  # Your prediction key

capture_from_camera_and_predict(output_folder, frame_interval, endpoint, prediction_key)
