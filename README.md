# ChatGPT + Enterprise data with Azure OpenAI

This sample demonstrates a few approaches for creating ChatGPT-like experiences over your own data. It uses Azure OpenAI Service to access the ChatGPT model (gpt-35-turbo and gpt3), and vector store (Pinecone, Redis and others) or Azure cognitive search for data indexing and retrieval.

The repo provides a way to upload your own data so it's ready to try end to end. 

## Features

* Upload (PDF Documents as well as Webpages), Chat and Q&A interfaces
* Explores various options to help users evaluate the trustworthiness of responses with citations, tracking of source content, etc.
* Shows possible approaches for data preparation, prompt construction, and orchestration of interaction between model (ChatGPT) and retriever (Cognitive Search)
* Settings directly in the UX to tweak the behavior and experiment with options (Coming soon)

## Architecture
![RAG Architecture](/Chatbot.png)

## Getting Started

** NOTE ** In order to deploy and run this example, you'll need an Azure subscription with access enabled for the Azure OpenAI service. You can request access [here](https://aka.ms/oaiapply).

### Prerequisites

- Coming soon
- 
### Installation

Starting from scratch:
1. Git clone the repo
2. Deploy all the resources (Script - Coming soon)
   1. Deploy Azure Open AI Service
      1. Create Davinci, Embedding and GPT3.5 Turbo deployment (https://learn.microsoft.com/en-us/azure/cognitive-services/openai/chatgpt-quickstart?tabs=command-line&pivots=programming-language-studio)
   2. Create Azure Storage Account (to host your documents)
   3. Create a free pinecone vectorstore database (https://www.pinecone.io/ and signup for free database)
3. Open VSCode and deploy api/Python to Azure Functions (Guide available at https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators)
   1. Update the Azure functions configuration settings with the resource information you deployed earlier.  Sample Settings are available at sample.settings.json
   2. If running locally, ensure you run pip install -r requirements.txt to install all packages
4. Go to app/frontend and run "npm run install"
   1. copy env.example to .env (for localhost running) and .env.prod for production deployment.
   2. Provide the information on the Azure Function URL
5. Validate running locally using "npm run dev"
6. Go to app/frontend and run "npm run build" 
   1. It will create the static files in app/backend/static folder
7. Deploy the app/backend to Azure Web App
   1. If running locally ensure you run pip install -r requirements.txt followed by py(python) app.py

### Quickstart

* In Azure: navigate to the Azure WebApp deployed by azd. The URL is printed out when azd completes (as "Endpoint"), or you can find it in the Azure portal.
* Running locally: navigate to 127.0.0.1:5000

Once in the web app:
* Try different topics in chat or Q&A context. For chat, try follow up questions, clarifications, ask to simplify or elaborate on answer, etc.
* Explore citations and sources
* Click on "settings" to try different options, tweak prompts, etc.

## Resources

* [Revolutionize your Enterprise Data with ChatGPT: Next-gen Apps w/ Azure OpenAI and Cognitive Search](https://aka.ms/entgptsearchblog)
* [Azure Cognitive Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
* [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/overview)

### Note
>Adapted from the Azure OpenAI Search repo at https://github.com/Azure-Samples/azure-search-openai-demo/