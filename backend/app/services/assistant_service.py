from typing import Any
from app.rag.service import RAGService
from app.services.chat_service import ChatService
from app.services.router_service import RouterService

class AssistantService:
    def __init__(self) -> None:
        self.router = RouterService()
        self.chat_service = ChatService()
        self.rag_service = RAGService()

    async def responder(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not messages:
            raise ValueError(
                "É necessário fornecer pelo menos uma mensagem."
            )

        ultima_mensagem = messages[-1]

        if ultima_mensagem.get("role") != "user":
            raise ValueError(
                "A última mensagem deve ser do usuário."
            )

        pergunta = ultima_mensagem.get("content", "")

        rota = await self.router.classificar(pergunta)

        if rota == "bulas":
            resultado = await self.rag_service.responder(
                messages
            )

            return {
                "route": rota,
                **resultado,
            }

        resultado = await self.chat_service.responder(
            messages
        )

        return {
            "route": rota,
            **resultado,
        }