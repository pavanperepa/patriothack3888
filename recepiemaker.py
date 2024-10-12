from azure.cosmos import CosmosClient
import os
from openai import AzureOpenAI

# Azure Cosmos DB connection details
cosmos_endpoint = os.getenv("COSMOSDB_ENDPOINT", "")
cosmos_key = os.getenv("COSMOSDB_KEY", "")
database_name = ""
container_name = ""

# Initialize CosmosDB client
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database = cosmos_client.get_database_client(database_name)
container = database.get_container_client(container_name)

# Fetching ingredients from CosmosDB
def get_ingredients():
    query = "SELECT * FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    # Assuming the ingredients are stored in the 'name' field
    ingredients_list = [item['name'] for item in items]
    
    return ingredients_list

# Fetch ingredients from the database
ingredients = get_ingredients()

# If we successfully fetched ingredients, format them into a prompt for the AI
if ingredients:
    ingredients_str = ', '.join(ingredients)
    print(f"Fetched ingredients: {ingredients_str}")

    # Initialize Azure OpenAI client with key-based authentication
    endpoint = os.getenv("ENDPOINT_URL", "")
    deployment = os.getenv("DEPLOYMENT_NAME", "")
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "")

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version="2024-05-01-preview",
    )

    # Create a completion based on fetched ingredients
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "You are an AI chef who creates unique and delicious recipes based on a given list of ingredients. Ensure the recipe is both reasonable and appetizing."
            },
            {
                "role": "user",
                "content": (
                    f"Create a recipe using the following ingredients: {ingredients_str}. "
                    "The Cheerios and peanut butter mixture should be used as a crunchy topping or garnish for the dish. "
                    "Make sure the recipe makes culinary sense and results in something tasty. If the ingredients do not make sense together, omit or substitute ingredients as necessary."
                )
            }
        ],
        max_tokens=800,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False
    )

    # Print out the generated recipe (using the correct dot notation)
    print(completion.choices[0].message.content)

else:
    print("No ingredients found in the database.")
