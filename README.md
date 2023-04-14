# ChatGPT + Enterprise data with Azure OpenAI

This sample demonstrates a few approaches for creating ChatGPT-like experiences over your own data. It uses Azure OpenAI Service to access the ChatGPT model (gpt-35-turbo and gpt3), and vector store (Pinecone, Redis and others) or Azure cognitive search for data indexing and retrieval.

The repo provides a way to upload your own data so it's ready to try end to end.

## Updates

* 3/16/2023 - Initial Release, Ask your Data and Chat with your Data
* 3/17/2023
  * Support uploading Multiple documents
  * Bug fix - Redis Vectorstore Implementation
* 3/18/2023 - API to generate summary on documents & Sample QA
* 3/19/2023 - Add GPT3 Chat Implementation
* 3/23/2023 - Add Cognitive Search as option to store documents
* 3/29/2023 - Automated Deployment script
* 4/8/2023 - Ask your SQL - Using [SQL Database Agent](https://python.langchain.com/en/latest/modules/agents/toolkits/examples/sql_database.html) or Using [SQL Database Chain](https://python.langchain.com/en/latest/modules/chains/examples/sqlite.html)
* 4/13/2023 - Add new feature to support asking questions on multiple document using [Vector QA Agent](https://python.langchain.com/en/latest/modules/agents/toolkits/examples/vectorstore.html)

## Test Website

[Chat and Ask over your data](https://dataaipdfchat.azurewebsites.net/)

## Features

* Upload (PDF/Text Documents as well as Webpages).  **New** - Connectors support.  Connect to your data directly from the Azure Container or a specific file.   You can also connect to AWS S3 Bucket & key.
![Upload](/assets/Upload.png)
* Chat - Chat to your document (GPT3 or ChatGpt)
![Chat](/assets/Chat.png)
* Q&A interfaces
![Ask](/assets/Ask.png)
* SQL Agent - Talk to your databases using Natural language.  This use-case showcases how using the prompt engineering approach from Chain of Thought modelling we can make it scalable and further use LLM capability of generating SQL Code from Natural Language by providing the context without the need to know the DB schema before hand.
![SqlAgent](/assets/SqlAgent.png)
* Edgar Analysis **Coming Soon** - Talk to & Search all SEC documents
![Edgar](/assets/Edgar.png)
* Developer Settings - Developer configurations and settings that can be configured for your dataset
![Developer](/assets/Developer.png)
* Explores various options to help users evaluate the trustworthiness of responses with citations, tracking of source content, etc.
![Thoughts](/assets/Thoughts.png)
* Shows possible approaches for data preparation, prompt construction, and orchestration of interaction between model (ChatGPT) and retriever
* Integration with Cognitive Search and Vector stores (Redis, Pinecone)

## Architecture

![Architecture](/assets/Chatbot.png)

## Getting Started

**NOTE** In order to deploy and run this example, you'll need an Azure subscription with access enabled for the Azure OpenAI service. You can request access [here](https://aka.ms/oaiapply).

### Prerequisites

#### To Run Locally

* [Azure Developer CLI](https://aka.ms/azure-dev/install)
* [Python 3.9](https://www.python.org/downloads/)
* [Node.js](https://nodejs.org/en/download/)
* [Git](https://git-scm.com/downloads)
* [ODBC Driver 17 for SQL](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16)
* [Azure Functions Extension for VSCode](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
* [Azure Functions Core tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
* [Powershell 7+ (pwsh)](https://github.com/powershell/powershell) - For Windows users only. **Important**: Ensure you can run `pwsh.exe` from a PowerShell command. If this fails, you likely need to upgrade PowerShell.

### Installation

1. Deploy the required Azure Services - Using scripts and steps below: 
   1. Git clone the repo
   2. Download the pre-requisites above
   3. Run `azd login` to login to Azure using your credentials
   4. Run `azd init` to initialize the environment name, subscription & location
      1. enter environment name, select subscription & location
   5. Run `azd env set AZURE_PREFIX <PrefixName>`  - Replace prefix name that will be used during deployment
   6. Run `azd up` to deploy the infrastructure code (azure services) and deploy the Azure functions as well as Backend app

   **Note** Ensure that the location you select is the location where OpenAI service is available to deploy (https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
      1. Above command will deploy following services
         1. Azure App Service Plan (Linux - B1 Tier)
         2. Cognitive Search Service (Standard Tier)
         3. Azure App Service (To Deploy backend service)
         4. Azure Function app (For all Python API)
         5. Storage Account (to store all your files) & Function storage account
         6. Azure Open AI Service
         7. Azure Application Insight
   
   **Note** External vector store are not deployed and you will need to manually deploy them (Pinecone or Redis)
2. Alternatively deploy the following services manually
   1. [OpenAI service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal).   Please be aware of the model & region availability documented [here]
(https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
   1. [Storage Account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal) and a container
   2. One of the Document Store
      1. [Pinecone Starter](https://www.pinecone.io/pricing/).  **Note** Make sure you create the index in Pincone with dimensions as 1536 and metric as cosine
      2. [Cognitive Search](https://learn.microsoft.com/en-us/azure/search/search-create-service-portal)
      3. Redis
   3. Create Function App (https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-function-app-portal)
   4. Create Azure Web App
   5. Git clone the repo
   6. Open the cloned repo folder in VSCode
   7. Open new terminal and go to /app/frontend directory
   8. Run `npm install` to install all the packages
   9.  Go to /api/Python directory
   10. Run `pip install -r requirements.txt` to install all required python packages
   11. Copy sample.settings.json to local.settings.json
   12. Update the configuration (Minimally you need OpenAi, one of the document store, storage account)
   13. Deploy the Azure Python API to Function app
   14. Open new terminal and go to /app/frontend directory
   15. Run npm run build for production build and copying static files to app/backend/static directory
   16. Open new terminal and go to /app/backend directory
   17. Copy env.example to .env file and edit the file to enter the Python localhost API and the storage configuration
   18. Deploy the app/backend Azure web app.


### Run Locally
   
1. Git clone the repo
2. Open the cloned repo folder in VSCode
3. Open new terminal and go to /app/frontend directory
4. Run `npm install` to install all the packages
5.  Go to /api/Python directory
6.  Run `pip install -r requirements.txt` to install all required python packages
7.  Copy sample.settings.json to local.settings.json
8.  Update the configuration (Minimally you need OpenAi, one of the document store, storage account)
9.  Start the Python API by running `func host start`
10. Open new terminal and go to /app/backend directory
12. Copy env.example to .env file and edit the file to enter the Python localhost API and the storage configuration
13. Run py app.py to start the backend locally (on port 5000)
19. Open new terminal and go to /app/frontend directory
20. Run npm run dev to start the local server (on port 5173)
21. Browse the localhost:5173 to open the web app.

Once in the web app:

* Try different topics in chat or Q&A context. For chat, try follow up questions, clarifications, ask to simplify or elaborate on answer, etc.
* Explore citations and sources
* Click on "settings" to try different options, tweak prompts, etc.

## Resources

* [Revolutionize your Enterprise Data with ChatGPT: Next-gen Apps w/ Azure OpenAI and Cognitive Search](https://aka.ms/entgptsearchblog)
* [Azure Cognitive Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
* [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/overview)

### Note

>Adapted from the Azure OpenAI Search repo at [OpenAI-CogSearch](https://github.com/Azure-Samples/azure-search-openai-demo/)
