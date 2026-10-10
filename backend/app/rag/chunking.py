from typing import Any

def _encontrar_fim_chunk(
    texto: str,
    inicio: int,
    tamanho: int,
) -> int:
    fim_maximo = min(inicio + tamanho, len(texto))

    if fim_maximo >= len(texto):
        return len(texto)

    trecho = texto[inicio:fim_maximo]

    pontos_de_corte = [
        trecho.rfind("\n\n"),
        trecho.rfind(". "),
        trecho.rfind(";\n"),
        trecho.rfind("\n"),
    ]

    melhor_corte = max(pontos_de_corte)

    limite_minimo = int(tamanho * 0.70)

    if melhor_corte >= limite_minimo:
        return inicio + melhor_corte + 1

    return fim_maximo


def criar_chunks(
    documentos: list[dict[str, str]],
    tamanho: int = 1800,
    sobreposicao: int = 250,
) -> list[dict[str, Any]]:
    if tamanho <= 0:
        raise ValueError("O tamanho do chunk deve ser maior que zero.")

    if sobreposicao < 0 or sobreposicao >= tamanho:
        raise ValueError(
            "A sobreposição deve ser maior ou igual a zero "
            "e menor que o tamanho do chunk."
        )

    chunks: list[dict[str, Any]] = []

    for documento in documentos:
        texto = documento["text"].strip()
        source = documento["source"]

        inicio = 0
        chunk_index = 0

        while inicio < len(texto):
            fim = _encontrar_fim_chunk(
                texto=texto,
                inicio=inicio,
                tamanho=tamanho,
            )

            trecho = texto[inicio:fim].strip()

            if trecho:
                chunks.append(
                    {
                        "text": trecho,
                        "source": source,
                        "chunk_index": chunk_index,
                    }
                )

                chunk_index += 1

            if fim >= len(texto):
                break

            proximo_inicio = fim - sobreposicao

            if proximo_inicio <= inicio:
                proximo_inicio = fim

            inicio = proximo_inicio

    return chunks