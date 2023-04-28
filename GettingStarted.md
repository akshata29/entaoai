# Getting Started

**NOTE** In order to deploy and run this example, you'll need an Azure subscription with access enabled for the Azure OpenAI service. You can request access [here](https://aka.ms/oaiapply).

Before to jumping to the Azure OpenAI API, this guide will show how to have access to Azure OpenAI services in your Azure Subscription as well the step by step on how to setup this service. [here](https://github.com/hcmarque/AzureOpenAI)

## Prerequisites

### To Run Locally

* [Azure Developer CLI](https://aka.ms/azure-dev/install)
* [Python 3.9](https://www.python.org/downloads/)
* [Node.js](https://nodejs.org/en/download/)
* [Git](https://git-scm.com/downloads)
* [ODBC Driver 17 for SQL](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16)
* [Azure Functions Extension for VSCode](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
* [Azure Functions Core tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
* [Powershell 7+ (pwsh)](https://github.com/powershell/powershell) - For Windows users only. **Important**: Ensure you can run `pwsh.exe` from a PowerShell command. If this fails, you likely need to upgrade PowerShell.

### Pre-build docker Image - API

Configure your `.env` as described in as described in [Configuration](Configuration.md).  You can alternatively, copy .dockerenv.example to .env from api\Python folder

Then run:

```console
docker run --env-file .env -p 7071:80 --name chataskapi -it akshata13/chataskapi:latest
```

Verify http://localhost:7071 to confirm the API is running locally.

### Pre-build docker Image - Application

Configure your `.env` as described in as described in [Configuration](Configuration.md).  You can alternatively, copy .dockerenv.example to .env from app\backend folder

Then run:

```console
docker run --env-file .env --name chataskapp -it akshata13/chataskapp:latest
```

Verify http://localhost:5000 to confirm the App is running locally.

### Installation

1. Deploy the required Azure Services - Using scripts and steps below:
   1. Git clone the repo
   2. Download the pre-requisites above
   3. Run `azd login` to login to Azure using your credentials
   4. Run `azd init` to initialize the environment name, subscription & location (If you already have the environment setup and want to create a new environment you can run instead `azd env new <name>`)
      1. enter environment name, select subscription & location
   5. Run `azd env set AZURE_PREFIX <PrefixName>`  - Replace prefix name that will be used during deployment
   6. Run `azd up` to deploy the infrastructure code (azure services) and deploy the Azure functions as well as Backend app

   **Note** Ensure that the location you select is the location where OpenAI service is available to [deploy](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
      1. Above command will deploy following services
         1. Azure App Service Plan (Linux - B1 Tier)
         2. Cognitive Search Service (Standard Tier)
         3. Azure App Service (To Deploy backend service)
         4. Azure Function app (For all Python API)
         5. Storage Account (to store all your files) & Function storage account
         6. Azure Open AI Service
         7. Azure Application Insight

   **Note** External vector store are not deployed and you will need to manually deploy them (Pinecone or Redis)
2. Semi-Automated Installation
   1. Click [![Deployment to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fakshata29%2Fchatpdf%2Fmain%2FDeployment%2Fazuredeploy.json) to deploy following services
      1. Azure App Service Plan (Linux - B1 Tier)
      2. Cognitive Search Service (Standard Tier)
      3. Azure App Service (To Deploy backend service)
      4. Azure Function app (For all Python API)
      5. Storage Account (to store all your files) & Function storage account
      6. Azure Open AI Service
      7. Azure Application Insight
      8. Cognitive Services (Language and Speech Service)
      9. SQL Server and Database (**Note** - SQL Script - northwind.sql need to run manually once database is created)
   2. [Fork the repo](https://github.com/akshata29/chatpdf/fork)
      1. **Note - Following information need to be performed only once**
      2. Click on Actions and select "I understand my workflow, go ahead and enable them"
      3. Download the [Publish Profile](https://github.com/Azure/functions-action#using-publish-profile-as-deployment-credential-recommended) for the Azure Function App that is deployed
      4. Setup AZURE_FUNCTIONAPP_PUBLISH_PROFILE secret in your forked repository (Settings -> Secrets and Variables -> Actions -> New Repository Secret).  Copy/Paste the content of the Publish profile
      5. Download the [Publish Profile](https://docs.microsoft.com/en-us/azure/app-service/deploy-github-actions?tabs=applevel#generate-deployment-credentials) for your Azure Web App. You can download this file from the Overview page of your Web App in the Azure Portal.
      6. Create a secret in your repository named AZURE_WEBAPP_PUBLISH_PROFILE, paste the publish profile contents as the value of the secret.  More [Information](https://docs.microsoft.com/azure/app-service/deploy-github-actions#configure-the-github-secret)
      7. Setup AZURE_FUNCTIONAPP_NAME secret in your forked repository as the name of your Function App
      8. Setup AZURE_WEBAPP_NAME secret in your forked repository as the name of your Azure App Service
   3. Successful execution of both workflow will deploy the Python API and Azure App Services (UI application)

3. Alternatively deploy the following services manually
   1. [OpenAI service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal).   Please be aware of the model & region availability documented [here]
(https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
   1. [Storage Account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal) and a container
   2. One of the Document Store
      1. [Pinecone Starter](https://www.pinecone.io/pricing/).  **Note** Make sure you create the index in Pincone with dimensions as 1536 and metric as cosine
      2. [Cognitive Search](https://learn.microsoft.com/en-us/azure/search/search-create-service-portal)
      3. Redis
   3. Create [Function App](https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-function-app-portal)
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
5. Go to /api/Python directory
6. Run `pip install -r requirements.txt` to install all required python packages
7. Copy sample.settings.json to local.settings.json
8. Update the configuration (Minimally you need OpenAi, one of the document store, storage account)
9. Start the Python API by running `func host start`
10. Open new terminal and go to /app/backend directory
11. Copy env.example to .env file and edit the file to enter the Python localhost API and the storage configuration
12. Run py app.py to start the backend locally (on port 5000)
13. Open new terminal and go to /app/frontend directory
14. Run npm run dev to start the local server (on port 5173)
!5. Browse the localhost:5173 to open the web app.

Once in the web app:

* Try different topics in chat or Q&A context. For chat, try follow up questions, clarifications, ask to simplify or elaborate on answer, etc.
* Explore citations and sources
* Click on "settings" to try different options, tweak prompts, etc.
  
