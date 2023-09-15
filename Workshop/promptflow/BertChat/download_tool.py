from promptflow import tool
from Chat.download import download


@tool
def download_tool(url: str, env_ready_signal: str) -> str:
    return download(url)
