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
* 4/17/2023 - Real-time Speech Analytics and Speech to Text and Text to Speech for Chat & Ask Features. (You can configure Text to Speech feature from the Developer settings.  You will need Azure Speech Services)
* 4/21/2023 - Add SQL Query & SQL Data tab to SQL NLP and fix Citations & Follow-up questions for Chat & Ask features
* 4/25/2023 - Initial version of Power Virtual Agent
* 4/28/2023 - Fix Bugs, Citations & Follow-up questions across QA & Chat.  Prompt bit more restrictive to limit responding from the document.
* 4/29/2023 - AWS S3 Process Integration using S3, AWS Lambda Function and Azure Data Factory (automated deployment not available yet, scripts are available in /Deployment/aws folder)
  
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

### Note

>Adapted from the Azure OpenAI Search repo at [OpenAI-CogSearch](https://github.com/Azure-Samples/azure-search-openai-demo/)
