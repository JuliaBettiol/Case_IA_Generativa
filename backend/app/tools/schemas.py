from typing import Literal
from pydantic import BaseModel, Field

SimNao = Literal["SIM", "NÃO"]

class BuscarFiliaisInput(BaseModel):
    localidade: str | None = Field(
        default=None,
        description="Cidade onde a filial está localizada, por exemplo LONDRINA.",
    )
    tipo_estabelecimento: str | None = Field(
        default=None,
        description="Tipo de estabelecimento, por exemplo BAIRRO ou CENTRO.",
    )
    delivery: SimNao | None = Field(
        default=None,
        description="Filtra filiais que possuem ou não delivery.",
    )
    panvel_clinic: SimNao | None = Field(
        default=None,
        description="Filtra filiais que possuem ou não serviços Panvel Clinic.",
    )
    estacionamento: SimNao | None = Field(
        default=None,
        description="Filtra filiais que possuem ou não estacionamento.",
    )
    atendimento_24_horas: SimNao | None = Field(
        default=None,
        description="Filtra filiais que possuem ou não atendimento 24 horas.",
    )

class ObterFilialInput(BaseModel):
    codigo_filial: str = Field(
        description="Identificador único da filial Panvel.",
    )