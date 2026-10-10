import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from app.models.chat import ChatRequest
from app.services.router_service import RouterService
from app.rag.service import RAGService
from app.services.assistant_service import AssistantService

router = APIRouter(prefix="/api", tags=["stream"])

router_service = RouterService()
rag_service = RAGService()
assistant_service = AssistantService()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
) -> EventSourceResponse:

    messages = [
        message.model_dump()
        for message in request.messages
    ]

    async def event_generator():
        try:
            pergunta = messages[-1]["content"]

            rota = await router_service.classificar(
                pergunta
            )

            # RAG com streaming real
            if rota == "bulas":
                async for evento in rag_service.stream_resposta(
                    messages
                ):
                    if evento["type"] == "metadata":
                        metadata = {
                            "route": "bulas",
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

                yield {
                    "event": "done",
                    "data": json.dumps(
                        {},
                        ensure_ascii=False,
                    ),
                }

                return

            # Filiais com streaming real
            async for evento in (
                assistant_service.chat_service.stream_resposta(
                    messages
                )
            ):
                if evento["type"] == "metadata":
                    metadata = {
                        "route": "filiais",
                        "tool_calls": evento["data"].get(
                            "tool_calls",
                            [],
                        ),
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

            yield {
                "event": "done",
                "data": json.dumps(
                    {},
                    ensure_ascii=False,
                ),
            }

        except Exception:
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "message":
                            "Erro ao processar a mensagem."
                    },
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(
        event_generator()
    )