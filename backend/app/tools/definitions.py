from app.tools.schemas import BuscarFiliaisInput, ObterFilialInput

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_filiais",
            "description": (
                "Busca filiais da Panvel usando dados estruturados. "
                "Pode filtrar por cidade, tipo de estabelecimento, delivery, "
                "Panvel Clinic, estacionamento e atendimento 24 horas."
            ),
            "parameters": BuscarFiliaisInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obter_filial",
            "description": (
                "Obtém os dados completos de uma filial específica da Panvel "
                "a partir do código da filial."
            ),
            "parameters": ObterFilialInput.model_json_schema(),
        },
    },
]