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

    if "OpenAiChat16k" in os.environ: 
        OpenAiChat16k = os.getenv('OpenAiChat16k')
    else:
        OpenAiChat16k = "chat16k"

    if "KbIndexName" in os.environ: 
        KbIndexName = os.environ['KbIndexName']
    else:
        KbIndexName = "aoaikb"

    if "OpenAiEvaluatorContainer" in os.environ: 
        OpenAiEvaluatorContainer = os.environ['OpenAiEvaluatorContainer']
    else:
        OpenAiEvaluatorContainer = "evaluator"

    if "OpenAiSummaryContainer" in os.environ: 
        OpenAiSummaryContainer = os.environ['OpenAiSummaryContainer']
    else:
        OpenAiSummaryContainer = "summary"

    if "FmpKey" in os.environ: 
        FmpKey = os.getenv('FmpKey')
    else:
        FmpKey = ""
    
    if "SecExtractionUrl" in os.environ: 
        SecExtractionUrl = os.getenv('SecExtractionUrl')
    else:
        SecExtractionUrl = ""

    if "SecDocPersistUrl" in os.environ: 
        SecDocPersistUrl = os.getenv('SecDocPersistUrl')
    else:
        SecDocPersistUrl = ""
    
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

    if "CosmosEndpoint" in os.environ: 
        CosmosEndpoint = os.environ['CosmosEndpoint']
    else:
        CosmosEndpoint = ""

    if "CosmosKey" in os.environ: 
        CosmosKey = os.environ['CosmosKey']
    else:
        CosmosKey = ""
    
    if "CosmosDatabase" in os.environ: 
        CosmosDatabase = os.environ['CosmosDatabase']
    else:
        CosmosDatabase = ""

    if "CosmosContainer" in os.environ: 
        CosmosContainer = os.environ['CosmosContainer']
    else:
        CosmosContainer = ""

    if "OpenAiEmbedding" in os.environ: 
        OpenAiEmbedding = os.environ['OpenAiEmbedding']
    else:
        OpenAiEmbedding = "embedding"

    if "UploadPassword" in os.environ: 
        UploadPassword = os.environ['UploadPassword']
    else:
        UploadPassword = "P@ssw0rd"

    if "AdminPassword" in os.environ: 
        AdminPassword = os.environ['AdminPassword']
    else:
        AdminPassword = "P@ssw0rd"

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
