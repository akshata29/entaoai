from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from typing import List
import re
from langchain.docstore.document import Document
import logging

def chunk_paragraphs(paragraphs: List[str], fullPath:str,  max_words: int = 300) -> List[Document]:
    """
    Chunk a list of paragraphs into chunks
    of approximately equal word count.
    """
    # Create a list of dictionaries with the paragraph as the
    # key and the word count as the value
    paragraphs = [{p: len(p.split())} for p in paragraphs]
    # Create a list of lists of paragraphs
    chunks = []
    # Iterate over the list of paragraphs
    for i, p in enumerate(paragraphs):
        # If the current chunk is empty, add the first paragraph to it
        if len(chunks) == 0:
            chunks.append([p])
        # If the current chunk is not empty, check if adding the
        # next paragraph will exceed the max word count
        else:
            # If adding the next paragraph will exceed the max word count,
            # start a new chunk
            if (
                sum([list(c.values())[0] for c in chunks[-1]]) + list(p.values())[0]
                > int(max_words)
            ):
                chunks.append([p])
            # If adding the next paragraph will not exceed the max word
            # count, add it to the current chunk
            else:
                chunks[-1].append(p)
    # Create a list of strings from the list of lists of paragraphs
    chunks = [" ".join([list(c.keys())[0] for c in chunk]) for chunk in chunks]

    logging.info(f"Number of chunks: {len(chunks)}")

    docs = [
            Document(page_content=result)
            for result in chunks
        ]
    for doc in docs:
        doc.metadata['source'] = fullPath
    return docs


    logging.info("Analyze Pre-built Layout")
    postUrl = endpoint + "documentintelligence/documentModels/prebuilt-layout:analyze?api-version=2023-10-31-preview"
    postUrl = postUrl + "&stringIndexType=utf16CodeUnit&pages=1&outputContentFormat=markdown"

    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': key
    }

    params = {
        "includeTextDetails": True,
        "pages" : 1,
        "features":["keyValuePairs","queryFields"]

    }

    with open(pathAndFile, "rb") as f:
        dataBytes = f.read()

    try:
        response = post(url=postUrl, data=dataBytes, headers=headers)
        if response.status_code != 202:
            logging.info("POST Analyze failed")
            return None
        getUrl = response.headers['Operation-Location']
    except Exception as e:
        logging.info("POST analyzed failed" + str(e))
        return None
    
    nTries = 50
    nTry = 0
    waitSec = 6

    while nTry < nTries:
        try:
            getResponse  = get(url=getUrl, headers=headers)
            respJson = json.loads(getResponse.text)
            if (getResponse.status_code != 200):
                print("Layout Get Failed")
                return None
            status = respJson["status"]
            if status == "succeeded":
                fileName = os.path.basename(pathAndFile).replace(".png", ".json")
                #print("store to", destinationPath + fileName)
                with open(destinationPath + fileName, "w") as f:
                    json.dump(respJson, f, indent=4, default=str)
                return respJson
            if status == "failed":
                logging.info("Analysis Failed")
                return None
            time.sleep(waitSec)
            nTry += 1
        except Exception as e:
            print("Exception during GET" + str(e))
            logging.info("Exception during GET" + str(e))
            return None

def analyze_layout(data: bytes, fullpath:str, endpoint: str, key: str, chunkSize: int) -> List[Document]:
    """
    Analyze a document with the layout model.

    Args:
        data (bytes): Document data.
        endpoint (str): Endpoint URL.
        key (str): API key.

    Returns:
        List[str]: List of paragraphs.
    """
    # Create a client for the form recognizer service
    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
    # Analyze the document with the layout model
    poller = document_analysis_client.begin_analyze_document("prebuilt-layout", data)
    # Get the results and extract the paragraphs
    # (title, section headings, and body)
    result = poller.result()
    
    paragraphs = [
        p.content
        for p in result.paragraphs
        if p.role in ["Title", "SectionHeading", "PageNumber", "PageFooter", "PageHeader", None]
    ]
    # Chunk the paragraphs (max word count = 100)
    logging.info(f"Number of paragraphs: {len(paragraphs)}")
    paragraphs = chunk_paragraphs(paragraphs, fullpath, chunkSize)

    return paragraphs

def normalize_text(s: str) -> str:
    """
    Clean up a string by removing redundant
    whitespaces and cleaning up the punctuation.

    Args:
        s (str): The string to be cleaned.

    Returns:
        s (str): The cleaned string.
    """
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r". ,", "", s)
    s = s.replace("..", ".")
    s = s.replace(". .", ".")
    s = s.replace("\n", "")
    s = s.strip()

    return s

