import re

from typing import Any

from app.llm.openai_provider import OpenAIProvider
from app.rag.medication_validator import MedicationValidator
from app.rag.query_rewriter import QueryRewriter
from app.rag.retriever import Retriever

from app.observability.timing import medir_etapa_async


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

10. Ao final da resposta, inclua uma seção "Fontes" contendo somente
    os nomes exatos dos arquivos das bulas que efetivamente sustentam
    informações apresentadas na resposta.

11. Cada fonte deve ser escrita exatamente como aparece no contexto,
    incluindo a extensão .pdf.

12. Não cite uma fonte que não tenha sido fornecida no contexto.

13. Não cite uma bula apenas porque ela foi recuperada. Cite somente
    as fontes efetivamente utilizadas para sustentar a resposta.

14. Não altere, abrevie ou invente nomes de arquivos de fontes.
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

    @staticmethod
    def _fontes_recuperadas(
        documentos: list[dict[str, Any]],
    ) -> list[str]:
        return list(
            dict.fromkeys(
                documento["source"]
                for documento in documentos
            )
        )

    @staticmethod
    def _extrair_fontes_citadas(
        resposta: str,
        fontes_disponiveis: list[str],
    ) -> list[str]:
        resposta_normalizada = resposta.casefold()

        return [
            fonte
            for fonte in fontes_disponiveis
            if fonte.casefold() in resposta_normalizada
        ]

    @staticmethod
    def _mensagem_sem_documentos(
        validation: str,
    ) -> str:
        if validation == "medicamento_indisponivel":
            return (
                "Não encontrei esse medicamento nas bulas "
                "disponíveis para consulta."
            )

        if validation == "orientacao_individual":
            return (
                "Não posso indicar qual medicamento, dose ou "
                "tratamento você deve utilizar com base nas bulas "
                "disponíveis. Para uma orientação individualizada, "
                "procure avaliação de um profissional de saúde."
            )

        return (
            "Não encontrei informações suficientes nas bulas "
            "disponíveis para responder com segurança."
        )

    @staticmethod
    def _remover_secao_fontes(
        resposta: str,
    ) -> str:
        padrao = re.compile(
            r"\n*\s*(?:#{1,6}\s*)?"
            r"(?:\*\*)?fontes?(?:\*\*)?\s*:?\s*"
            r"(?:\n.*)*$",
            flags=re.IGNORECASE,
        )

        return re.sub(
            padrao,
            "",
            resposta,
        ).rstrip()

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

        async with medir_etapa_async("query_rewrite_ms"):
            pergunta_busca = await self.query_rewriter.reescrever(
                messages
            )

        async with medir_etapa_async("medication_validation_ms"):
            validacao = await self.medication_validator.validar(
                pergunta_busca
            )

        if validacao in {
            "medicamento_indisponivel",
            "orientacao_individual",
        }:
            return {
                "messages": [],
                "retrieved_documents": [],
                "search_query": pergunta_busca,
                "validation": validacao,
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

        return {
            "messages": llm_messages,
            "retrieved_documents": documentos,
            "search_query": pergunta_busca,
            "validation": validacao,
        }

    async def stream_resposta(
        self,
        messages: list[dict[str, Any]],
    ):
        contexto = await self.preparar_contexto(
            messages
        )

        documentos = contexto["retrieved_documents"]

        fontes_disponiveis = self._fontes_recuperadas(
            documentos
        )

        yield {
            "type": "metadata",
            "data": {
                "sources": [],
                "search_query": contexto["search_query"],
                "retrieved_documents": self._documentos_publicos(
                    documentos
                ),
            },
        }

        if not documentos:
            yield {
                "type": "content",
                "data": {
                    "text": self._mensagem_sem_documentos(
                        contexto["validation"]
                    ),
                },
            }
            return

        resposta_completa = ""
        usage = None

        async with medir_etapa_async("llm_generation_ms"):
            async for evento in self.provider.stream_chat(
                contexto["messages"]
            ):
                if evento["type"] == "content":
                    texto = evento["data"]["text"]

                    resposta_completa += texto

                    yield evento

                elif evento["type"] == "usage":
                    usage = evento["data"]

        fontes_citadas = self._extrair_fontes_citadas(
            resposta_completa,
            fontes_disponiveis,
        )

        yield {
            "type": "final_metadata",
            "data": {
                "sources": fontes_citadas,
            },
        }

        if usage:
            yield {
                "type": "usage",
                "data": usage,
            }

    async def responder(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:

        contexto = await self.preparar_contexto(
            messages
        )

        documentos = contexto["retrieved_documents"]

        if not documentos:
            return {
                "content": self._mensagem_sem_documentos(
                    contexto["validation"]
                ),
                "sources": [],
                "retrieved_documents": [],
                "search_query": contexto["search_query"],
                "usage": None,
            }

        async with medir_etapa_async("llm_generation_ms"):
            response = await self.provider.chat(
                messages=contexto["messages"],
            )

        message = response.message
        resposta = message.content or ""

        fontes_disponiveis = self._fontes_recuperadas(
            documentos
        )

        fontes_citadas = self._extrair_fontes_citadas(
            resposta,
            fontes_disponiveis,
        )

        return {
            "content": resposta,
            "sources": fontes_citadas,
            "retrieved_documents": documentos,
            "search_query": contexto["search_query"],
            "usage": (
                response.usage.to_dict()
                if response.usage
                else None
            ),
        }