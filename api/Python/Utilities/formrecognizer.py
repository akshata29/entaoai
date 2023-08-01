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

