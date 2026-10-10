from typing import Any, Callable
from app.tools.filiais import buscar_filiais, obter_filial
from app.tools.schemas import BuscarFiliaisInput, ObterFilialInput

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "buscar_filiais": {
        "function": buscar_filiais,
        "schema": BuscarFiliaisInput,
    },
    "obter_filial": {
        "function": obter_filial,
        "schema": ObterFilialInput,
    },
}

def executar_tool(nome: str, argumentos: dict[str, Any]) -> Any:
    tool = TOOL_REGISTRY.get(nome)

    if tool is None:
        raise ValueError(f"Tool desconhecida: {nome}")

    schema = tool["schema"]
    function: Callable[..., Any] = tool["function"]

    argumentos_validados = schema(**argumentos)

    return function(argumentos_validados)