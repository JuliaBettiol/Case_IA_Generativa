from typing import Any
from app.llm.openai_provider import OpenAIProvider
from app.rag.query_rewriter import QueryRewriter
from app.rag.retriever import Retriever


RAG_SYSTEM_PROMPT = """
Você é um assistente da Panvel especializado em responder perguntas
sobre medicamentos com base exclusivamente nas bulas fornecidas.

REGRAS:

1. Responda somente com informações presentes no contexto recuperado.

2. Não invente informações que não estejam nos trechos fornecidos.

3. Se o contexto não for suficiente para responder com segurança,
   diga claramente que não encontrou informação suficiente nas bulas
   disponíveis.

4. Não faça diagnóstico médico.

5. Não prescreva medicamentos, doses ou tratamentos individualizados.

6. Diferencie informações documentais da bula de orientação médica
   individual.

7. Quando houver riscos graves descritos no contexto, deixe claro que
   situações graves exigem avaliação profissional.

8. Ao final da resposta, inclua uma seção "Fonte" citando exatamente
   o nome do arquivo da bula fornecido no contexto.

9. Não cite uma fonte que não tenha sido fornecida no contexto.
"""


class RAGService:
    def __init__(self) -> None:
        self.retriever = Retriever()
        self.provider = OpenAIProvider()
        self.query_rewriter = QueryRewriter()

    async def preparar_contexto(
            self,
            messages: list[dict[str, Any]],
        ) -> dict[str, Any]:
            if not messages:
                raise ValueError(
                    "É necessário fornecer pelo menos uma mensagem."
                )

            pergunta_original = messages[-1].get(
                "content",
                "",
            )

            pergunta_busca = await self.query_rewriter.reescrever(
                messages
            )

            documentos = await self.retriever.buscar(
                pergunta_busca
            )

            contexto = "\n\n".join(
                (
                    f"[Fonte: {documento['source']} | "
                    f"Chunk: {documento['chunk_index']}]\n"
                    f"{documento['text']}"
                )
                for documento in documentos
            )

            llm_messages = [
                {
                    "role": "system",
                    "content": RAG_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"PERGUNTA ORIGINAL:\n"
                        f"{pergunta_original}\n\n"
                        f"PERGUNTA CONTEXTUALIZADA:\n"
                        f"{pergunta_busca}\n\n"
                        f"CONTEXTO DAS BULAS:\n"
                        f"{contexto}"
                    ),
                },
            ]

            sources = list(
                dict.fromkeys(
                    documento["source"]
                    for documento in documentos
                )
            )

            return {
                "messages": llm_messages,
                "sources": sources,
                "retrieved_documents": documentos,
                "search_query": pergunta_busca,
            }

    async def stream_resposta(
        self,
        messages: list[dict[str, Any]],
    ):
        contexto = await self.preparar_contexto(
            messages
        )

        yield {
            "type": "metadata",
            "data": {
                "sources": contexto["sources"],
                "search_query": contexto["search_query"],
                "retrieved_documents": contexto[
                    "retrieved_documents"
                ],
            },
        }

        async for chunk in self.provider.stream_chat(
            contexto["messages"]
        ):
            yield {
                "type": "content",
                "data": {
                    "text": chunk,
                },
            }

    async def responder(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not messages:
            raise ValueError(
                "É necessário fornecer pelo menos uma mensagem."
            )

        pergunta_original = messages[-1].get(
            "content",
            "",
        )

        pergunta_busca = await self.query_rewriter.reescrever(
            messages
        )

        documentos = await self.retriever.buscar(
            pergunta_busca
        )

        if not documentos:
            return {
                "content": (
                    "Não encontrei informações suficientes "
                    "nas bulas disponíveis."
                ),
                "sources": [],
                "retrieved_documents": [],
                "search_query": pergunta_busca,
                "usage": None,
            }

        contexto = "\n\n".join(
            (
                f"[Fonte: {documento['source']} | "
                f"Chunk: {documento['chunk_index']}]\n"
                f"{documento['text']}"
            )
            for documento in documentos
        )

        llm_messages = [
            {
                "role": "system",
                "content": RAG_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"PERGUNTA ORIGINAL:\n"
                    f"{pergunta_original}\n\n"
                    f"PERGUNTA CONTEXTUALIZADA:\n"
                    f"{pergunta_busca}\n\n"
                    f"CONTEXTO DAS BULAS:\n"
                    f"{contexto}"
                ),
            },
        ]

        response = await self.provider.chat(
            messages=llm_messages,
        )

        message = response.choices[0].message

        sources = list(
            dict.fromkeys(
                documento["source"]
                for documento in documentos
            )
        )

        return {
            "content": message.content,
            "sources": sources,
            "retrieved_documents": documentos,
            "search_query": pergunta_busca,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            if response.usage
            else None,
        }