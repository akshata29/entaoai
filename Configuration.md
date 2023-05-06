# Configuration

## API Configuration

| Key | Default Value | Detail |
| --- | --- | ------------- |
|OpenAiKey||Your Azure OpenAI Key.  <br>You can get the OpenAI Key from Azure Portal for your deployed OpenAI service.
|OpenAiService||Name of the OpenAI Service deployed in Azure
|OpenAiEndPoint||Fully qualified endpoint for Azure OpenAI <br>(https://<yourresource>.openai.azure.com/)
|OpenAiVersion|2022-12-01|API Version of the Azure OpenAI
|OpenAiDavinci|davinci|Deployment name of text-davinci-003 <br>model in Azure OpenAI
|OpenAiEmbedding|text-embedding-ada-002|Deployment name of <br>text-embedding-ada-002 model in Azure OpenAI
|MaxTokens|500|Maximum Tokens
|Temperature|0.3|Temperature
|OpenAiChat|chat|Deployment name of gpt-35-turbo model in <br>Azure OpenAI
|PineconeKey|key|Pinecone Key
|PineconeEnv|env|Pinecone Environment
|VsIndexName|oaiembed|Pinecone Index name
|RedisPassword|Password|Redis Password
|RedisAddress|localhost|Redis URI
|RedisPort|6379|Redis Port
|OpenAiDocStorName||Document Storage account name
|OpenAiDocStorKey||Document Storage Key
|OpenAiDocContainer|chatpdf|Document storage container name
|SearchService||Azure Cognitive Search service name
|SearchKey||Azure Cognitive Search service Admin Key
|SecDocContainer|secdoc|Document Storage container to <br>store SEC documents
|SynapseName||Name of the SQL for SQL NLP (Azure SQL, Synapse)
|SynapsePool||Database or SQL Pool Name
|SynapseUser||SQL User name
|SynapsePassword||SQL Password
|UploadPassword||Password required for upload functionality.
|AdminPassword||Password required for Admin capabilities.
|DOCGENERATOR_URL|Optional Settings|Required only if you are planning to use the AWS Integration.
|*PROMPTS*||Default Prompts for Speech Analytics Use-case. <br>26 Keys with different prompt.

## Application Configuration

| Key | Default Value | Detail |
| --- | --- | ------------- |
AGENTQA_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/AgentQa?code=<yourcode>)
BLOB_CONNECTION_STRING||Blob Connection string for the storage account
BLOB_CONTAINER_NAME||Blob container name where all PDF are uploaded
CHAT3_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/Chat?code=<yourcode>)
CHAT_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/ChatGpt?code=<yourcode>)
DOCGENERATOR_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/DocGenerator?code=<yourcode>)
INDEXMANAGEMENT_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/IndexManagement?code=<yourcode>)
QA_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/QuestionAnswering?code=<yourcode>)
SECSEARCH_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/SecSearch?code=<yourcode>)
SPEECH_KEY||Speech Service Key
SPEECH_REGION||Region where speech service is deployed <br> (i.e. eastus, southcentralus)
SQLCHAIN_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/SqlChain?code=<yourcode>)
SQLCHAT_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/SqlChat?code=<yourcode>)
SUMMARIZER_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/Summarizer?code=<yourcode>)
SUMMARYQA_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/SampleQaSummary?code=<yourcode>)
TASKAGENTQA_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/TaskAgentQa?code=<yourcode>)
TEXTANALYTICS_KEY||Text Analytics(Language) Service Key
TEXTANALYTICS_REGION||Region where Text Analytics(Language) is deployed <br> (i.e. eastus, southcentralus)
VERIFYPASS_URL||Azure Function URL with host/default key <br> (https://<yourfunction>.azurewebsites.net/api/VerifyPassword?code=<yourcode>)
