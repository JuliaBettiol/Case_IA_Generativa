from typing import Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)

class ToolCallInfo(BaseModel):
    name: str
    arguments: dict

class RetrievedDocument(BaseModel):
    score: float
    source: str
    chunk_index: int
    text: str

class ChatResponse(BaseModel):
    route: Literal["filiais", "bulas"]
    content: str
    tool_calls: list[ToolCallInfo] = []
    sources: list[str] = []
    retrieved_documents: list[RetrievedDocument] = []
    search_query: str | None = None
    usage: dict | None = None