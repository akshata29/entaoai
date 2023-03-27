# ChatGPT + Enterprise data with Azure OpenAI

This sample demonstrates a few approaches for creating ChatGPT-like experiences over your own data. It uses Azure OpenAI Service to access the ChatGPT model (gpt-35-turbo and gpt3), and vector store (Pinecone, Redis and others) or Azure cognitive search for data indexing and retrieval.

The repo provides a way to upload your own data so it's ready to try end to end.

## Features

* Upload (PDF/Text Documents as well as Webpages)
![Upload](/assets/Upload.png)
* Chat
![Chat](/assets/Chat.png)
* Q&A interfaces
![Ask](/assets/Ask.png)
* Explores various options to help users evaluate the trustworthiness of responses with citations, tracking of source content, etc.
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
* [Azure Functions Extension for VSCode](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
* [Azure Functions Core tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools)
* [Powershell 7+ (pwsh)](https://github.com/powershell/powershell) - For Windows users only. **Important**: Ensure you can run `pwsh.exe` from a PowerShell command. If this fails, you likely need to upgrade PowerShell.

### Installation

1. Deploy the required Azure Services - Using *Semi-Automated* scripts and steps below: 
   1. az deployment sub create --location <location>  --template-file main.bicep --parameters prefix=<prefix></prefix> resourceGroupName=<rgName> location=<location>
      1. Ensure that the location you select is the location where OpenAI service is available to deploy (https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
      2. Above command will deploy following services
         1. Azure App Service Plan (Linux - B1 Tier)
         2. Cognitive Search Service (Standard Tier)
         3. Azure App Service (To Deploy backend service)
         4. Azure Function app (For all Python API)
         5. Storage Account (to store all your files)
         6. Azure Open AI Service
      3. As a part of the deployment it will also create the application configuration settings (some of them are pre-populated and rest for now you will need to add value manually) (Both for the Azure Function and Azure Web App)
      4. Once the services are deployed, zip the files (in the api\Python folder) and name it as Deploy.zip
      5. Run following command to deploy the Azure Function to the app you created.
         1. az functionapp deployment source config-zip -g <rgbane> -n <prefix>func --src .\Deploy.zip
2. Alternatively deploy the following services manually
   1. [OpenAI service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal).   Please be aware of the model & region availability documented [here]
(https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models#model-summary-table-and-region-availability)
   1. [Storage Account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal) and a container
   2. One of the Document Store
      1. [Pinecone Starter](https://www.pinecone.io/pricing/)
      2. [Cognitive Search](https://learn.microsoft.com/en-us/azure/search/search-create-service-portal)
      3. Redis
   3. Create Function App (https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-function-app-portal)
   4. Create Azure Web App
   5. Git clone the repo
   6. Open the cloned repo folder in VSCode
   8. Open new terminal and go to /app/frontend directory
   9. Run `npm install` to install all the packages
   10. Go to /api/Python directory
   11. Run `pip install -r requirements.txt` to install all required python packages
   12. Copy sample.settings.json to local.settings.json
   13. Update the configuration (Minimally you need OpenAi, one of the document store, storage account)
   14. Deploy the Azure Python API to Function app
   15. Open new terminal and go to /api/frontend directory
   16. Run npm run build for production build and copying static files to app/backend/static directory
   17. Open new terminal and go to /api/backend directory
   18. Copy env.example to .env file and edit the file to enter the Python localhost API and the storage configuration
   19. Deploy the app/backend Azure web app.


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
10. Open new terminal and go to /api/backend directory
12. Copy env.example to .env file and edit the file to enter the Python localhost API and the storage configuration
13. Run py app.py to start the backend locally (on port 5000)
19. Open new terminal and go to /api/frontend directory
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