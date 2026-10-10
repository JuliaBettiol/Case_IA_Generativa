from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.assistant_service import AssistantService
from app.observability.tracing import TraceContext
from app.observability.logger import log_error, log_turn

router = APIRouter(
    prefix="/api",
    tags=["chat"],
)

assistant_service = AssistantService()

@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest) -> ChatResponse:
    trace = TraceContext()

    try:
        messages = [
            message.model_dump()
            for message in request.messages
        ]

        resultado = await assistant_service.responder(
            messages
        )

        log_turn(
            trace_id=trace.trace_id,
            route=resultado["route"],
            latency_ms=trace.elapsed_ms(),
            usage=resultado.get("usage"),
            tool_calls=resultado.get("tool_calls", []),
            sources=resultado.get("sources", []),
            retrieved_documents=resultado.get(
                "retrieved_documents",
                [],
            ),
        )

        return ChatResponse(
            route=resultado["route"],
            content=resultado["content"],
            tool_calls=resultado.get(
                "tool_calls",
                [],
            ),
            sources=resultado.get(
                "sources",
                [],
            ),
            retrieved_documents=resultado.get(
                "retrieved_documents",
                [],
            ),
            search_query=resultado.get(
                "search_query",
            ),
            usage=resultado.get(
                "usage",
            ),
            trace_id=trace.trace_id,
            latency_ms=trace.elapsed_ms(),
        )

    except Exception as exc:
        log_error(
            trace_id=trace.trace_id,
            latency_ms=trace.elapsed_ms(),
            error=exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a mensagem.",
        ) from exc