from openai import AzureOpenAI
# Azure OpenAI API setup
API_KEY = ""

client = AzureOpenAI(
    api_key=API_KEY,
    api_version='2024-04-01-preview',
    azure_endpoint='https://azure-openai-api-eastus2.openai.azure.com/',
    azure_deployment='gpt-4o-2024-05-13'
)

if not client.api_key:
    raise ValueError("The Azure OpenAI API key has not been set in the environment variables.")
