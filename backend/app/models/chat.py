from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)


class ToolCallInfo(BaseModel):
    name: str
    arguments: dict[str, Any]


class RetrievedDocument(BaseModel):
    score: float
    source: str
    chunk_index: int
    text: str


class ChatResponse(BaseModel):
    route: Literal["filiais", "bulas"]
    content: str
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    retrieved_documents: list[RetrievedDocument] = Field(
        default_factory=list
    )
    search_query: str | None = None
    usage: dict[str, Any] | None = None
    trace_id: str | None = None
    latency_ms: float | None = None