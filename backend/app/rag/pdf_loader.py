from pathlib import Path
from pypdf import PdfReader

def extrair_texto_pdf(caminho: Path) -> str:
    reader = PdfReader(caminho)

    paginas: list[str] = []

    for pagina in reader.pages:
        texto = pagina.extract_text()

        if texto:
            paginas.append(texto.strip())

    return "\n\n".join(paginas)

def carregar_bulas(diretorio: Path) -> list[dict[str, str]]:
    if not diretorio.exists():
        raise FileNotFoundError(
            f"Diretório de bulas não encontrado: {diretorio}"
        )

    documentos: list[dict[str, str]] = []

    for caminho in sorted(diretorio.glob("*.pdf")):
        texto = extrair_texto_pdf(caminho)

        documentos.append(
            {
                "source": caminho.name,
                "text": texto,
            }
        )

    return documentos