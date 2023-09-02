from typing import List
from promptflow import tool
from embeddingstore.core.contracts import SearchResultEntity
from langchain.docstore.document import Document
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

@tool
def generate_prompt_context(search_result: List[dict]) -> str:
    retrieved_docs = []
    for item in search_result:

        entity = SearchResultEntity.from_dict(item)
        content  = entity.text or ""
        source = entity.original_entity['sourcefile']
        docId = entity.original_entity['id']
        
        retrieved_docs.append(Document(page_content=content, metadata={"id": docId, "source": source}))
    return retrieved_docs
