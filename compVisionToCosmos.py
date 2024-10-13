from azure.cosmos import CosmosClient
import requests
import json

# Custom Vision API credentials
custom_vision_endpoint = "place_holder"
custom_vision_prediction_key = "place_holder"
image_path = "place_holder"  # Path to your input image

# Azure Cosmos DB credentials
cosmos_endpoint = "place_holder"
cosmos_key = "place_holder"
database_name = "place_holder"
container_name = "place_holder"

# Connect to Cosmos DB
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database = cosmos_client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Step 1: Send the image to Custom Vision for prediction
def get_custom_vision_predictions(image_path):
    with open(image_path, "rb") as image_data:
        headers = {
            "Prediction-Key": custom_vision_prediction_key,
            "Content-Type": "application/octet-stream"
        }
        response = requests.post(custom_vision_endpoint, headers=headers, data=image_data)
        
        # Error handling if response is not successful
        if response.status_code != 200:
            print(f"Error from Custom Vision: {response.status_code} - {response.text}")
            return None
        return response.json()

# Step 2: Store the prediction results in Cosmos DB
def store_in_cosmos_db(prediction_results):
    if "error" in prediction_results:
        print(f"Error from Custom Vision: {prediction_results['error']['message']}")
        return
    
    if "predictions" in prediction_results:
        for prediction in prediction_results["predictions"]:
            grocery_item = {
                "id": prediction["tagName"] + "-" + str(prediction["probability"]),  # Unique ID
                "name": prediction["tagName"],
                "probability": prediction["probability"],
                "quantity": 1,  # Assuming 1 detected object (modify as needed)
                "location": "fridge",  # Assuming fridge camera, modify as needed
                "detectedFrom": "camera",
                "status": "fresh"
            }
            container.create_item(grocery_item)
            print(f"Inserted item: {grocery_item['name']} with confidence {grocery_item['probability']}")
    else:
        print("No predictions found in the response.")

# Main function to handle Custom Vision output and store in Cosmos DB
if __name__ == "__main__":
    # Get predictions from Custom Vision
    predictions = get_custom_vision_predictions(image_path)
    
    if predictions is not None:
        print("Predictions received from Custom Vision:", predictions)

        # Store results in Cosmos DB
        store_in_cosmos_db(predictions)
    else:
        print("Failed to get predictions from Custom Vision.")
