import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.models.chat import ChatRequest
from app.services.router_service import RouterService
from app.rag.service import RAGService
from app.services.assistant_service import AssistantService

from app.observability.tracing import TraceContext
from app.observability.logger import log_error, log_turn
from app.observability.token_tracker import (
    iniciar_contagem,
    obter_tokens,
    finalizar_contagem,
)
from app.observability.timing import (
    iniciar_medicao,
    obter_latencias,
    finalizar_medicao,
    medir_etapa_async,
)


router = APIRouter(
    prefix="/api",
    tags=["stream"],
)

router_service = RouterService()
rag_service = RAGService()
assistant_service = AssistantService()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
) -> EventSourceResponse:

    trace = TraceContext()

    messages = [
        message.model_dump()
        for message in request.messages
    ]

    if not messages or messages[-1]["role"] != "user":
        raise ValueError(
            "A última mensagem deve ser do usuário."
        )

    async def event_generator():
        token_contexto = iniciar_contagem()
        timing_contexto = iniciar_medicao()

        try:
            pergunta = messages[-1]["content"]

            rota = await router_service.classificar(
                pergunta
            )

            # ==========================================
            # ROTA RAG — BULAS
            # ==========================================
            if rota == "bulas":
                usage = None
                sources = []
                retrieved_documents = []

                async for evento in rag_service.stream_resposta(
                    messages
                ):
                    if evento["type"] == "metadata":
                        sources = evento["data"].get(
                            "sources",
                            [],
                        )

                        retrieved_documents = evento["data"].get(
                            "retrieved_documents",
                            [],
                        )

                        metadata = {
                            "route": "bulas",
                            "trace_id": trace.trace_id,
                            **evento["data"],
                        }

                        yield {
                            "event": "metadata",
                            "data": json.dumps(
                                metadata,
                                ensure_ascii=False,
                            ),
                        }

                    elif evento["type"] == "content":
                        yield {
                            "event": "content",
                            "data": json.dumps(
                                evento["data"],
                                ensure_ascii=False,
                            ),
                        }

                    elif evento["type"] == "final_metadata":
                        sources = evento["data"].get(
                            "sources",
                            [],
                        )

                        yield {
                            "event": "metadata",
                            "data": json.dumps(
                                {
                                    "route": "bulas",
                                    "trace_id": trace.trace_id,
                                    "sources": sources,
                                },
                                ensure_ascii=False,
                            ),
                        }

                    elif evento["type"] == "usage":
                        usage = evento["data"]

                usage_total = obter_tokens() or usage
                stage_latencies = obter_latencias()
                latency_ms = trace.elapsed_ms()

                log_turn(
                    trace_id=trace.trace_id,
                    route="bulas",
                    latency_ms=latency_ms,
                    stage_latencies_ms=stage_latencies,
                    usage=usage_total,
                    tool_calls=[],
                    sources=sources,
                    retrieved_documents=retrieved_documents,
                )

                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "trace_id": trace.trace_id,
                            "latency_ms": latency_ms,
                            "stage_latencies_ms": stage_latencies,
                            "usage": usage_total,
                        },
                        ensure_ascii=False,
                    ),
                }

                return

            # ==========================================
            # ROTA TOOLS — FILIAIS
            # ==========================================
            usage = None
            tool_calls = []

            async with medir_etapa_async(
                "tool_orchestration_ms"
            ):
                async for evento in (
                    assistant_service.chat_service.stream_resposta(
                        messages
                    )
                ):
                    if evento["type"] == "metadata":
                        tool_calls = evento["data"].get(
                            "tool_calls",
                            [],
                        )

                        metadata = {
                            "route": "filiais",
                            "trace_id": trace.trace_id,
                            "tool_calls": tool_calls,
                            "sources": [],
                            "search_query": None,
                        }

                        yield {
                            "event": "metadata",
                            "data": json.dumps(
                                metadata,
                                ensure_ascii=False,
                            ),
                        }

                    elif evento["type"] == "content":
                        yield {
                            "event": "content",
                            "data": json.dumps(
                                evento["data"],
                                ensure_ascii=False,
                            ),
                        }

                    elif evento["type"] == "usage":
                        usage = evento["data"]

            usage_total = obter_tokens() or usage
            stage_latencies = obter_latencias()
            latency_ms = trace.elapsed_ms()

            log_turn(
                trace_id=trace.trace_id,
                route="filiais",
                latency_ms=latency_ms,
                stage_latencies_ms=stage_latencies,
                usage=usage_total,
                tool_calls=tool_calls,
                sources=[],
                retrieved_documents=[],
            )

            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "trace_id": trace.trace_id,
                        "latency_ms": latency_ms,
                        "stage_latencies_ms": stage_latencies,
                        "usage": usage_total,
                    },
                    ensure_ascii=False,
                ),
            }

        except Exception as exc:
            log_error(
                trace_id=trace.trace_id,
                latency_ms=trace.elapsed_ms(),
                stage_latencies_ms=obter_latencias(),
                error=exc,
            )

            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "message": "Erro ao processar a mensagem.",
                        "trace_id": trace.trace_id,
                    },
                    ensure_ascii=False,
                ),
            }

        finally:
            finalizar_medicao(timing_contexto)
            finalizar_contagem(token_contexto)

    return EventSourceResponse(
        event_generator()
    )