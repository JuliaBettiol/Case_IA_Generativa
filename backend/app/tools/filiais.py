from decimal import Decimal
from pathlib import Path
from typing import Any
import pandas as pd
from app.core.config import get_settings
from app.tools.schemas import BuscarFiliaisInput, ObterFilialInput

settings = get_settings()

DATA_PATH = Path(settings.data_dir).resolve() / "filiais.parquet"

def _carregar_filiais() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de filiais não encontrado em: {DATA_PATH}"
        )

    return pd.read_parquet(DATA_PATH)

def _serializar_valor(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return str(valor)

    if pd.isna(valor):
        return None

    if hasattr(valor, "item"):
        return valor.item()

    return valor

def _serializar_registro(registro: dict[str, Any]) -> dict[str, Any]:
    return {
        chave: _serializar_valor(valor)
        for chave, valor in registro.items()
    }

def buscar_filiais(args: BuscarFiliaisInput) -> list[dict[str, Any]]:
    df = _carregar_filiais()

    filtros = args.model_dump(exclude_none=True)

    for coluna, valor in filtros.items():
        if coluna in {"localidade", "tipo_estabelecimento"}:
            df = df[
                df[coluna].astype(str).str.upper()
                == str(valor).strip().upper()
            ]
        else:
            df = df[df[coluna] == valor]

    registros = df.to_dict(orient="records")

    return [_serializar_registro(registro) for registro in registros]

def obter_filial(args: ObterFilialInput) -> dict[str, Any] | None:
    df = _carregar_filiais()

    resultado = df[
        df["codigo_filial"].astype(str)
        == str(args.codigo_filial).strip()
    ]

    if resultado.empty:
        return None

    registro = resultado.iloc[0].to_dict()

    return _serializar_registro(registro)