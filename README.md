# ChatGPT + Enterprise data with Azure OpenAI

This sample demonstrates a few approaches for creating ChatGPT-like experiences over your own data. It uses Azure OpenAI Service to access the ChatGPT model (gpt-35-turbo and gpt3), and vector store (Pinecone, Redis and others) or Azure cognitive search for data indexing and retrieval.

The repo provides a way to upload your own data so it's ready to try end to end.

## Updates

* 6/7/2023 - Add OpenAI Playground in Developer Tools and initial version of building the CoPilot (for now with Notebook, but eventually will be moved as CoPilot feature).  Add the script, recording and example for Real-time Speech analytics use-case.  More to be added soon.
* 5/27/2023 - Add Workshop content in the form of the notebooks that can be leveraged to learn/execute the scenarios.  You can find the notebooks in the [Workshop](Workshop) folder.  Details about workshop content is available [here](READMEWORKSHOP.md).
* 5/26/2023 - Add Summarization feature to summarize the document either using stuff, mapreduce or refine summarization.  To use this feature (on existing deployment) ensure you add the `OpenAiSummaryContainer` configuration to Function app and `BLOB_SUMMARY_CONTAINER_NAME` configuration to Azure App Service (Ensure that the value you enter is the same as the container name in Azure storage and that you have created the container).  You also need to add `PROCESSSUMMARY_URL` configuration to Azure App Service (Ensure that the value you enter is the same as the Azure Function URL).
* 5/24/2023 - Add feature to upload CSV files and CSV Agent to answer/chat questions on the tabular data.  Smart Agent also supports answering questions on CSV data.
* 5/22/2023 - Initial version of "Smart Agent" that gives you flexibility to talk to all documents uploaded in the solution.  It also allow you to talk to SQL Database Scenario.  As more features are added, agent will keep on building upon that (for instance talk to CSV/Excel or Tabular data)
* 5/21/2023 - Add Developer Tools section - Experimental code conversion and Prompt guru.
* 5/17/2023 - Change the edgar source to Cognitive search vector store instead of Redis.
* 5/15/2023 - Add the option to use "Cognitive Search" as Vector store for storing the index.  Azure Cognitive Search offers pure vector search and hybrid retrieval – as well as a sophisticated re-ranking system powered by Bing in a single integrated solution. [Sign-up](https://aka.ms/VectorSearchSignUp). Support uploading WORD documents.
* 5/10/2023 - Add the options on how document should be chunked.  If you want to use the Form Recognizer, ensure the Form recognizer resource is created and the appropriate application settings `FormRecognizerKey` and `FormRecognizerEndPoint` are configured.
* 5/07/2023 - Option available to select either Azure OpenAI or OpenAI.  For OpenAI ensure you have `OpenAiApiKey` in Azure Functions settings.  For Azure OpenAI you will need `OpenAiKey`, `OpenAiService` and `OpenAiEndPoint` Endpoint settings.  You can also select that option for Chat/Question/SQL Nlp/Speech Analytics and other features (from developer settings page).
* 5/03/2023 - Password required for Upload and introduced Admin page starting with Index Management
* 4/30/2023 - Initial version of Task Agent Feature added.  Autonomous Agents are agents that designed to be more long running. You give them one or multiple long term goals, and they independently execute towards those goals. The applications combine tool usage and long term memory.  Initial feature implements [Baby AGI](https://github.com/yoheinakajima/babyagi) with execution tools
* 4/29/2023 - AWS S3 Process Integration using S3, AWS Lambda Function and Azure Data Factory (automated deployment not available yet, scripts are available in /Deployment/aws folder)
* 4/28/2023 - Fix Bugs, Citations & Follow-up questions across QA & Chat.  Prompt bit more restrictive to limit responding from the document.
* 4/25/2023 - Initial version of Power Virtual Agent
* 4/21/2023 - Add SQL Query & SQL Data tab to SQL NLP and fix Citations & Follow-up questions for Chat & Ask features
* 4/17/2023 - Real-time Speech Analytics and Speech to Text and Text to Speech for Chat & Ask Features. (You can configure Text to Speech feature from the Developer settings.  You will need Azure Speech Services)
* 4/13/2023 - Add new feature to support asking questions on multiple document using [Vector QA Agent](https://python.langchain.com/en/latest/modules/agents/toolkits/examples/vectorstore.html)
* 4/8/2023 - Ask your SQL - Using [SQL Database Agent](https://python.langchain.com/en/latest/modules/agents/toolkits/examples/sql_database.html) or Using [SQL Database Chain](https://python.langchain.com/en/latest/modules/chains/examples/sqlite.html)
* 3/29/2023 - Automated Deployment script
* 3/23/2023 - Add Cognitive Search as option to store documents
* 3/19/2023 - Add GPT3 Chat Implementation
* 3/18/2023 - API to generate summary on documents & Sample QA
* 3/17/2023
  * Support uploading Multiple documents
  * Bug fix - Redis Vectorstore Implementation
* 3/16/2023 - Initial Release, Ask your Data and Chat with your Data

## Test Website

[Chat and Ask over your data](https://dataaipdfchat.azurewebsites.net/)

## Features

[List of Features](Features.md)

## Architecture

![Architecture](/assets/Chatbot.png)

## Azure Architecture

![Azure Services](/assets/AskChat.png)

## Getting Started

[Get Started](GettingStarted.md)

## Configuration

[Application and Function App Configuration](Configuration.md)

## Resources

* [Revolutionize your Enterprise Data with ChatGPT: Next-gen Apps w/ Azure OpenAI and Cognitive Search](https://aka.ms/entgptsearchblog)
* [Azure Cognitive Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
* [Azure OpenAI Service](https://learn.microsoft.com/azure/cognitive-services/openai/overview)
* [Redis Search](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/cache-redis-modules#redisearch)
* [Pinecone](https://www.pinecone.io/learn/pinecone-v2/)
* [Cognitive Search Vector Store](https://aka.ms/VectorSearchSignUp)
  
### Note

>Adapted from the Azure OpenAI Search repo at [OpenAI-CogSearch](https://github.com/Azure-Samples/azure-search-openai-demo/),  [Call Center Analytics](https://github.com/amulchapla/AI-Powered-Call-Center-Intelligence) and [Edgar Crawler](https://github.com/nlpaueb/edgar-crawler)
