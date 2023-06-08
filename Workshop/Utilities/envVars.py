import os
import logging
from dotenv import load_dotenv  

# Configure environment variables  
load_dotenv(dotenv_path='./.env')

try:
    OpenAiKey = os.getenv('OpenAiKey')
    OpenAiVersion = os.getenv('OpenAiVersion', "2023-05-15")
    OpenAiDavinci = os.getenv('OpenAiDavinci')
    OpenAiChat = os.getenv('OpenAiChat')
    OpenAiService = os.getenv('OpenAiService', '')
    OpenAiBase = f"https://{OpenAiService}.openai.azure.com"
    OpenAiDocStorName = os.getenv('OpenAiDocStorName')
    OpenAiDocStorKey = os.getenv('OpenAiDocStorKey')
    OpenAiDocConnStr = f"DefaultEndpointsProtocol=https;AccountName={OpenAiDocStorName};AccountKey={OpenAiDocStorKey};EndpointSuffix=core.windows.net"
    OpenAiDocContainer = os.getenv('OpenAiDocContainer')

    if "OpenAiSummaryContainer" in os.environ: 
        OpenAiSummaryContainer = os.getenv('OpenAiSummaryContainer')
    else:
        OpenAiSummaryContainer = "summary"

    if "SecDocContainer" in os.environ: 
        SecDocContainer = os.getenv('SecDocContainer')
    else:
        SecDocContainer = ""

    if "FmpKey" in os.environ: 
        FmpKey = os.getenv('FmpKey')
    else:
        FmpKey = ""

    if "PineconeEnv" in os.environ: 
        PineconeEnv = os.getenv('PineconeEnv')
    else:
        PineconeEnv = ""

    if "PineconeKey" in os.environ: 
        PineconeKey = os.getenv('PineconeKey')
    else:
        PineconeKey = ""

    if "VsIndexName" in os.environ: 
        VsIndexName = os.getenv('VsIndexName')
    else:
        VsIndexName = ""
        
    if "RedisAddress" in os.environ: 
        RedisAddress = os.getenv('RedisAddress')
    else:
        RedisAddress = ""

    if "RedisPassword" in os.environ: 
        RedisPassword = os.getenv('RedisPassword')
    else:
        RedisPassword = ""

    if "RedisPort" in os.environ: 
        RedisPort = os.getenv('RedisPort')
    else:
        RedisPort = ""

    if "SearchKey" in os.environ: 
        SearchKey = os.getenv('SearchKey')
    else:
        SearchKey = ""

    if "SearchIndex" in os.environ: 
        SearchIndex = os.getenv('SearchIndex')
    else:
        SearchIndex = ""

    if "SearchService" in os.environ: 
        SearchService = os.getenv('SearchService')
    else:
        SearchService = ""

    if "BingUrl" in os.environ: 
        BingUrl = os.getenv('BingUrl')
    else:
        BingUrl = ""

    if "BingKey" in os.environ: 
        BingKey = os.getenv('BingKey')
    else:
        BingKey = ""

    OpenAiEmbedding = os.getenv('OpenAiEmbedding')
    UploadPassword = os.getenv('UploadPassword') or ''
    AdminPassword = os.getenv('AdminPassword') or ''

    if "ChromaUrl" in os.environ: 
        ChromaUrl = os.getenv('ChromaUrl')
    else:
        ChromaUrl = ""

    if "ChromaPort" in os.environ: 
        ChromaPort = os.getenv('ChromaPort')
    else:
        ChromaPort = ""

    if "OpenAiApiKey" in os.environ: 
        OpenAiApiKey = os.getenv('OpenAiApiKey')
    else:
        OpenAiApiKey = ""

    if "FormRecognizerKey" in os.environ: 
        FormRecognizerKey = os.getenv('FormRecognizerKey')
    else:
        FormRecognizerKey = ""

    if "FormRecognizerEndPoint" in os.environ: 
        FormRecognizerEndPoint = os.getenv('FormRecognizerEndPoint')
    else:
        FormRecognizerEndPoint = ""
    
    if "SynapseName" in os.environ: 
        SynapseName = os.getenv('SynapseName')
    else:
        SynapseName = ""

    if "SynapseUser" in os.environ: 
        SynapseUser = os.getenv('SynapseUser')
    else:
        SynapseUser = ""

    if "SynapsePassword" in os.environ: 
        SynapsePassword = os.getenv('SynapsePassword')
    else:
        SynapsePassword = ""

    if "SynapsePool" in os.environ: 
        SynapsePool = os.getenv('SynapsePool')
    else:
        SynapsePool = ""
except Exception as e:
    print("Error reading environment variables: " + str(e))
