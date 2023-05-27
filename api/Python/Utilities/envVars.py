import os
import logging

try:
    OpenAiKey = os.environ['OpenAiKey']
    OpenAiVersion = os.environ['OpenAiVersion']
    OpenAiDavinci = os.environ['OpenAiDavinci']
    OpenAiChat = os.environ['OpenAiChat']
    OpenAiService = os.environ['OpenAiService']
    OpenAiDocStorName = os.environ['OpenAiDocStorName']
    OpenAiDocStorKey = os.environ['OpenAiDocStorKey']
    OpenAiDocConnStr = f"DefaultEndpointsProtocol=https;AccountName={OpenAiDocStorName};AccountKey={OpenAiDocStorKey};EndpointSuffix=core.windows.net"
    OpenAiDocContainer = os.environ['OpenAiDocContainer']

    if "OpenAiSummaryContainer" in os.environ: 
        OpenAiSummaryContainer = os.environ['OpenAiSummaryContainer']
    else:
        OpenAiSummaryContainer = "summary"

    if "SecDocContainer" in os.environ: 
        SecDocContainer = os.environ['SecDocContainer']
    else:
        SecDocContainer = ""

    if "PineconeEnv" in os.environ: 
        PineconeEnv = os.environ['PineconeEnv']
    else:
        PineconeEnv = ""

    if "PineconeKey" in os.environ: 
        PineconeKey = os.environ['PineconeKey']
    else:
        PineconeKey = ""

    if "VsIndexName" in os.environ: 
        VsIndexName = os.environ['VsIndexName']
    else:
        VsIndexName = ""
        
    if "RedisAddress" in os.environ: 
        RedisAddress = os.environ['RedisAddress']
    else:
        RedisAddress = ""

    if "RedisPassword" in os.environ: 
        RedisPassword = os.environ['RedisPassword']
    else:
        RedisPassword = ""

    if "RedisPort" in os.environ: 
        RedisPort = os.environ['RedisPort']
    else:
        RedisPort = ""

    if "SearchKey" in os.environ: 
        SearchKey = os.environ['SearchKey']
    else:
        SearchKey = ""

    if "SearchService" in os.environ: 
        SearchService = os.environ['SearchService']
    else:
        SearchService = ""

    if "BingUrl" in os.environ: 
        BingUrl = os.environ['BingUrl']
    else:
        BingUrl = ""

    if "BingKey" in os.environ: 
        BingKey = os.environ['BingKey']
    else:
        BingKey = ""

    OpenAiEmbedding = os.environ['OpenAiEmbedding']
    UploadPassword = os.environ['UploadPassword'] or ''
    AdminPassword = os.environ['AdminPassword'] or ''

    if "ChromaUrl" in os.environ: 
        ChromaUrl = os.environ['ChromaUrl']
    else:
        ChromaUrl = ""

    if "ChromaPort" in os.environ: 
        ChromaPort = os.environ['ChromaPort']
    else:
        ChromaPort = ""

    if "OpenAiApiKey" in os.environ: 
        OpenAiApiKey = os.environ['OpenAiApiKey']
    else:
        OpenAiApiKey = ""

    if "FormRecognizerKey" in os.environ: 
        FormRecognizerKey = os.environ['FormRecognizerKey']
    else:
        FormRecognizerKey = ""

    if "FormRecognizerEndPoint" in os.environ: 
        FormRecognizerEndPoint = os.environ['FormRecognizerEndPoint']
    else:
        FormRecognizerEndPoint = ""
    
    if "SynapseName" in os.environ: 
        SynapseName = os.environ['SynapseName']
    else:
        SynapseName = ""

    if "SynapseUser" in os.environ: 
        SynapseUser = os.environ['SynapseUser']
    else:
        SynapseUser = ""

    if "SynapsePassword" in os.environ: 
        SynapsePassword = os.environ['SynapsePassword']
    else:
        SynapsePassword = ""

    if "SynapsePool" in os.environ: 
        SynapsePool = os.environ['SynapsePool']
    else:
        SynapsePool = ""
except Exception as e:
    logging.info("Error reading environment variables: %s",e)
