from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ChatIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator('message')
    @classmethod
    def validar_mensagem(cls, valor):
        valor = valor.strip()
        if not valor:
            raise ValueError('A mensagem não pode estar vazia.')
        return valor


class Slots(BaseModel):
    nome: str | None = None
    placa: str | None = None
    data: str | None = None
    horario: str | None = None


class Sentimento(BaseModel):
    label: Literal['positivo', 'neutro', 'negativo']
    score: float = Field(ge=0, le=1)


class Resumo(BaseModel):
    dados: Slots
    intencao: str
    relato: str
    acoes: list[str]


class Handoff(BaseModel):
    active: bool = False
    reason: str | None = None
    summary: Resumo | None = None


class ChatOut(BaseModel):
    session_id: str
    reply: str
    intent: str
    slots: Slots
    sentiment: Sentimento
    fallback: bool
    handoff: Handoff
    turn: int
    latency_ms: float
    status: Literal['ativa', 'encerrada', 'transferida']
    guardrail_events: list[str] = []


class Mensagem(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class ModelIn(BaseModel):
    model: str = Field(min_length=1, max_length=200)


class ModelOut(BaseModel):
    id: str
    name: str


class SessionOut(BaseModel):
    model: str | None = None
    session_id: str
    greeting: str
    history: list[Mensagem]
    slots: Slots
    status: Literal['ativa', 'encerrada', 'transferida']
    handoff: Handoff
    turn: int
    last_turn: ChatOut | None = None


class FeedbackIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=1, le=5, strict=True)


class HealthOut(BaseModel):
    status: str
    provider: str
    model: str
    model_available: bool


class MetricsOut(BaseModel):
    total_conversas: int
    total_turnos: int
    conversas_encerradas_sem_handoff: int
    conversas_com_handoff: int
    turnos_fallback: int
    taxa_contencao: float
    taxa_fallback: float
    taxa_handoff: float
    mensagens_por_conversa: float
    latencia_media_ms: float
    eventos_guardrail: int
    csat_medio: float | None
    respostas_csat: int
    fallback_por_intencao: dict[str, int]
    erros_modelo: int


class HandoffOut(BaseModel):
    session_id: str
    handoff: Handoff
