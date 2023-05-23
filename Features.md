# Features

* Upload (PDF/Text Documents as well as Webpages).  **New** - Connectors support.  Connect to your data directly from the Azure Container or a specific file.   You can also connect to AWS S3 Bucket & key.  Integration with AWS S3 using AWS Lambda, Event grid and Azure Data factory.  Added support to upload to existing index and support document chunk process using different technique including Azure Form Recognizer.
![Upload](/assets/Upload.png)
* Chat - Chat to your document - ChatGpt
![ChatGpt](/assets/ChatGpt.png)
* Chat - Chat to your document - GPT 3
![Chat](/assets/Chat.png)
* Q&A interfaces
![Ask](/assets/Ask.png)
* Agent QA - Agents use an LLM to determine which actions to take and in what order. An action can either be using a tool and observing its output, or returning to the user. Agent QA showcases how to retrieve information from one or more vectorstores.
![AgentQA](/assets/AgentQA.png)
* SQL Agent - Talk to your databases using Natural language.  This use-case showcases how using the prompt engineering approach from Chain of Thought modelling we can make it scalable and further use LLM capability of generating SQL Code from Natural Language by providing the context without the need to know the DB schema before hand.
![SqlAgent](/assets/SqlAgent.png)
* Speech Analytics - Real-time transcription and analysis of a call to improve the customer experience by providing insights and suggest actions to agents. This can help with agent-assist and virtual agents use cases. Key technical components of this demo are:
  * Transcription of live audio stream using Azure Speech Service
  * Entity extraction + PII detection and redaction using Azure Language Service
  * Conversation summarization using Azure OpenAI Service
  * Extract business insights & conversation details using Azure OpenAI Service
![Speech](/assets/Speech.png)
* Edgar Analysis **Coming Soon** - Talk to & Search all SEC documents
![Edgar](/assets/Edgar.png)
* Developer Settings - Developer configurations and settings that can be configured for your dataset
![Developer](/assets/Developer.png)
* Tools to enhance developer productivity and experimental capabilities. Currently features available to convert the code and generate prompt for your use-case and scenarios.
![Developer Tools](/assets/DeveloperTools.png)
* Adminstration capabilities to manage your dataset, index, and other settings
![Admin](/assets/Admin.png)
* Explores various options to help users evaluate the trustworthiness of responses with citations, tracking of source content, etc.
![Thoughts](/assets/Thoughts.png)
* Shows possible approaches for data preparation, prompt construction, and orchestration of interaction between model (ChatGPT) and retriever
* Integration with Cognitive Search and Vector stores (Redis, Pinecone)
