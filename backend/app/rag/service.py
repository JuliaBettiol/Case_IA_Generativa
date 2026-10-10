from typing import Any

from app.llm.openai_provider import OpenAIProvider
from app.rag.medication_validator import MedicationValidator
from app.rag.query_rewriter import QueryRewriter
from app.rag.retriever import Retriever


RAG_SYSTEM_PROMPT = """
Você é um assistente da Panvel especializado em responder perguntas
sobre medicamentos com base exclusivamente nas bulas fornecidas.

REGRAS:

1. Responda somente com informações presentes no contexto recuperado.

2. Nunca use conhecimento externo ao contexto para complementar
   informações farmacológicas.

3. Não invente informações que não estejam nos trechos fornecidos.

4. Se o contexto não for suficiente para responder com segurança,
   diga claramente que não encontrou informação suficiente nas bulas
   disponíveis.

5. Não faça diagnóstico médico.

6. Não recomende qual medicamento o usuário deve tomar.

7. Não prescreva medicamentos, doses ou tratamentos individualizados.

8. Diferencie informações documentais da bula de orientação médica
   individual.

9. Quando houver riscos graves descritos no contexto, deixe claro que
   situações graves exigem avaliação profissional.

10. Ao final da resposta, inclua uma seção "Fonte" citando exatamente
    o nome do arquivo da bula fornecido no contexto.

11. Não cite uma fonte que não tenha sido fornecida no contexto.

12. Cite somente fontes que sustentem as informações apresentadas
    na resposta.
"""


class RAGService:
    def __init__(self) -> None:
        self.retriever = Retriever()
        self.provider = OpenAIProvider()
        self.query_rewriter = QueryRewriter()
        self.medication_validator = MedicationValidator()

    @staticmethod
    def _documentos_publicos(
        documentos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "source": documento["source"],
                "chunk_index": documento["chunk_index"],
                "score": documento["score"],
            }
            for documento in documentos
        ]

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

        validacao = await self.medication_validator.validar(
            pergunta_busca
        )

        if validacao in {
            "medicamento_indisponivel",
            "orientacao_individual",
        }:
            return {
                "messages": [],
                "sources": [],
                "retrieved_documents": [],
                "search_query": pergunta_busca,
            }

        documentos = await self.retriever.buscar(
            pergunta_busca,
            aplicar_threshold=(
                validacao != "consulta_geral_bulas"
            ),
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
        contexto = await self.preparar_contexto(messages)

        yield {
            "type": "metadata",
            "data": {
                "sources": contexto["sources"],
                "search_query": contexto["search_query"],
                "retrieved_documents": self._documentos_publicos(
                    contexto["retrieved_documents"]
                ),
            },
        }

        if not contexto["retrieved_documents"]:
            yield {
                "type": "content",
                "data": {
                    "text": (
                        "Não encontrei informações suficientes "
                        "nas bulas disponíveis para responder "
                        "com segurança."
                    ),
                },
            }
            return

        async for evento in self.provider.stream_chat(
            contexto["messages"]
        ):
            yield evento

    async def responder(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        contexto = await self.preparar_contexto(messages)

        if not contexto["retrieved_documents"]:
            return {
                "content": (
                    "Não encontrei informações suficientes "
                    "nas bulas disponíveis para responder "
                    "com segurança."
                ),
                "sources": [],
                "retrieved_documents": [],
                "search_query": contexto["search_query"],
                "usage": None,
            }

        response = await self.provider.chat(
            messages=contexto["messages"],
        )

        message = response.choices[0].message

        return {
            "content": message.content,
            "sources": contexto["sources"],
            "retrieved_documents": contexto[
                "retrieved_documents"
            ],
            "search_query": contexto["search_query"],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            if response.usage
            else None,
        }