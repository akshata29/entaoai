targetScope = 'subscription'

@minLength(1)
@description('Primary location for all resources')
param location string

@minLength(6)
@description('Prefix used for all resources')
param prefix string

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

param resourceGroupName string = '${prefix}rg'

param appServicePlanName string = '${prefix}asp'
param backendServiceName string = '${prefix}backend'
param functionAppName string = '${prefix}func'

param searchServiceName string = '${prefix}azs'
param searchServiceSkuName string = 'standard'

param storageAccountName string = '${prefix}stor'
param containerName string = 'chatpdf'

param openAiServiceName string = '${prefix}oai'
param applicationInsightsName string = '${prefix}appisg'

param openAiSkuName string = 'S0'

param chatGptDeploymentName string = 'chat'
param chatGptModelName string = 'gpt-35-turbo'
param textEmbeddingDeploymentName string = 'text-embedding-ada-002'
param textEmbeddingModelName string = 'text-embedding-ada-002'

var abbrs = loadJsonContent('abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${prefix}'
  location: location
  tags: tags
}

module monitoring 'core/monitor/applicationinsights.bicep' = {
  name: 'monitoring'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    name: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
  }
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      capacity: 1
    }
    kind: 'linux'
  }
}

module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: resourceGroup
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    publicNetworkAccess: 'Enabled'
    sku: {
      name: 'Standard_ZRS'
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: containerName
        publicAccess: 'None'
      }
      {
        name: 'secdoc'
        publicAccess: 'None'
      }
    ]
  }
}

module emptyfunction 'core/host/function.bicep' = {
  name: 'emptyfunction'
  scope: resourceGroup
  params: {
    name: !empty(functionAppName) ? functionAppName : '${abbrs.webSitesAppService}func-${resourceToken}'
    emptyFunction:true
    location: location
    appServicePlanId: appServicePlan.outputs.id
    tags: union(tags, { 'azd-service-name': 'functionapp' })
    runtimeName: 'python'
    runtimeVersion: '3.9'
    managedIdentity: true
    appSettings: {}
  }
}

module openAi 'core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  scope: resourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: openAiSkuName
    }
    deployments: [
      {
        name: chatGptDeploymentName
        model: {
          format: 'OpenAI'
          name: chatGptModelName
          version: '0301'
        }
        scaleSettings: {
          scaleType: 'Standard'
        }
      }
      {
        name: textEmbeddingDeploymentName
        model: {
          format: 'OpenAI'
          name: textEmbeddingModelName
          version: '1'
        }
        scaleSettings: {
          scaleType: 'Standard'
        }
      }
    ]
  }
}

module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  scope: resourceGroup
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'gptkb-${resourceToken}'
    location: location
    tags: tags
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: 'free'
  }
}


module function 'core/host/function.bicep' = {
  name: 'function'
  scope: resourceGroup
  dependsOn: [
    appServicePlan
    monitoring
    searchService
    storage
    openAi
  ]
  params: {
    name: !empty(functionAppName) ? functionAppName : '${abbrs.webSitesAppService}func-${resourceToken}'
    location: location
    emptyFunction:false
    appServicePlanId: appServicePlan.outputs.id
    tags: union(tags, { 'azd-service-name': 'functionapp' })
    runtimeName: 'python'
    runtimeVersion: '3.9'
    managedIdentity: true
    appSettings: {
      APPINSIGHTS_INSTRUMENTATIONKEY: monitoring.outputs.instrumentationKey
      APPLICATIONINSIGHTS_CONNECTION_STRING: monitoring.outputs.connectionString
      OpenAiEndPoint:openAi.outputs.endpoint
      OpenAiVersion:'2023-05-15'
      OpenAiEmbedding:textEmbeddingDeploymentName
      OpenAiKey:openAi.outputs.key
      MaxTokens:500
      Temperature:'0.3'
      OpenAiChat:chatGptDeploymentName
      PineconeKey:'key'
      PineconeEnv:'env'
      VsIndexName:'dummy'
      RedisPassword:'Password'
      RedisAddress:'http://localhost'
      RedisPort:'6379'
      OpenAiDocStorName:storage.outputs.name
      OpenAiDocStorKey:storage.outputs.key
      OpenAiDocContainer:containerName
      SearchService:searchService.outputs.name
      SearchKey:searchService.outputs.key
      SecDocContainer:'secdoc'
      SynapseName:'dummy'
      SynapsePool:'dummy'
      SynapseUser:'dummy'
      SynapsePassword:'dummy'
      RealTimeSpeechPrompt: '\'"\'"\'"Write a concise summary of the following: \r\n \r\n{text}\'"\'"\'"'
      RealTimeSpeechPromptIv: 'text'
      RtsInsurancePrompt: '\'"\'"\'"Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer\n3. Where the accident happened?\n4. How did the accident happen?\n5. What was the weather like when the accident happened?\n6. What is customer\'s phone number?\n7. Was the airbag deployed when accident happened? \r\n \r\n{text}\'"\'"\'"'
      RtsInsurancePromptIv: 'text'
      RtsBankingPrompt: '\'"\'"\'"Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer \r\n \r\n{text}\'"\'"\'"'
      RtsBankingPromptIv: 'text'
      RtsCapMarketPrompt: '\'"\'"\'"Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer \r\n \r\n{text}\'"\'"\'"'  
      RtsCapMarketPromptIv: 'text'
      RtsHealthcarePrompt: '\'"\'"\'"Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer\n3. What health condition was discussed? \n4. Was any medication mentioned in the conversation?\n5. Identify medical entities such as symptoms, medications, diagnosis from this conversaion. \r\n \r\n{text}\'"\'"\'"'
      RtsHealthcarePromptIv: 'text'
      RtsGeneralPrompt: '\'"\'"\'"Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer\n3. What are the action items and follow-ups? \r\n \r\n{text}\'"\'"\'"'
      RtsGeneralPromptIv: 'text'
      RtsSummaryNotesPrompt: '\'"\'"\'"Generate detailed call summary notes in list format from the following text \r\n \r\n{text}\'"\'"\'"'
      RtsSummaryNotesPromptIv: 'text'
      RtsParticipantsPrompt: '\'"\'"\'"Extract list of call participants in list format from the following text \r\n \r\n{text}\'"\'"\'"'
      RtsParticipantsPromptIv: 'text'
      RtsFollowupPrompt: '\'"\'"\'"Generate list of call follow up tasks from following text \r\n \r\n{text}\'"\'"\'"'
      RtsFollowupPromptIv: 'text'
      RtsPharmacyPrompt: '\'"\'"\'"Provide list of medications, dose, and form discussed in the following text \r\n \r\n{text}\'"\'"\'"'
      RtsPharmacyPromptIv: 'text'
      RtsPiiPrompt: '\'"\'"\'"List of all PII and named entities and what is overall sentiment of the conversation \r\n \r\n{text}\'"\'"\'"'
      RtsPiiPromptIv: 'text'
      RtsTopicsPrompt: '\'"\'"\'"Generate list of topics discussed from text \r\n \r\n{text}\'"\'"\'"'
      RtsTopicsPromptIv: 'text'
      RtsComplexPrompt: '\'"\'"\'"You must extract the following information from the phone conversation below: \n\n 1. Call reason (key: reason) \n 2. Cause of incident (key: cause) \n 3. Name of caller (key: caller) \n 4. Account number (key: account_id) \n 5. Follow-up Flag(key: followupind) \n 6. A short, yet detailed summary (key: summary) \n\n Make sure fields 1 to 4 are answered very short. Field 5 is a boolean flag which indicates whether the caller incident was resolved, 1 if follow up required, 0 if resolved.  Please answer in JSON machine-readable format, using the keys from above. Format the output as JSON object. Pretty print the JSON and make sure that is properly closed at the end. \r\n \r\n{text}\'"\'"\'"'
      RtsComplexPromptIv: 'text'
      OpenAiQuestionPrompt: '\'"\'"\'"Please reply to the question using only the information present in the text above. If you can\'t find it, reply \'Not in the text\'.\nQuestion: _QUESTION_\nAnswer:\'"\'"\'"'
    }
  }
}

// The application frontend
module backend 'core/host/appservice.bicep' = {
  name: 'backend'
  scope: resourceGroup
  dependsOn: [
    appServicePlan
    storage
    function
  ]
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    storageAccountName: storage.outputs.name
    tags: union(tags, { 'azd-service-name': 'backend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.9'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    appSettings: {
      AGENTQA_URL: '${function.outputs.uri}/AgentQa?code=${function.outputs.key}'
      QA_URL: '${function.outputs.uri}/QuestionAnswering?code=${function.outputs.key}'
      CHAT_URL: '${function.outputs.uri}/ChatGpt?code=${function.outputs.key}'
      DOCGENERATOR_URL: '${function.outputs.uri}/DocGenerator?code=${function.outputs.key}'
      SECSEARCH_URL: '${function.outputs.uri}/SecSearch?code=${function.outputs.key}'
      SQLCHAT_URL: '${function.outputs.uri}/SqlChat?code=${function.outputs.key}'
      SQLCHAIN_URL: '${function.outputs.uri}/SqlChain?code=${function.outputs.key}'
      BLOB_CONTAINER_NAME: containerName
      BLOB_CONNECTION_STRING: storage.outputs.connectionString
    }
  }
}


output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name

output AZURE_OPENAI_SERVICE string = openAi.outputs.name
output AZURE_OPENAI_CHATGPT_DEPLOYMENT string = chatGptDeploymentName

output AZURE_SEARCH_SERVICE string = searchService.outputs.name

output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_CONTAINER string = containerName

output BACKEND_URI string = backend.outputs.uri
