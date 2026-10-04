import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import APIKeyHeader
from app.schemas import ChatIn, ChatOut, SessionOut, FeedbackIn, HealthOut, MetricsOut, HandoffOut, ModelIn, ModelOut
from app.analytics.metrics import calcular_metricas
from app.llm.client import ModeloIndisponivel
from app.llm.models import opcoes

chave = APIKeyHeader(name='X-API-Key', auto_error=False)


def autenticar(request: Request, recebida: str | None = Depends(chave)):
    if not recebida or not secrets.compare_digest(recebida, request.app.state.bot.config.api_key):
        raise HTTPException(401, 'Chave de acesso inválida. Verifique a configuração da aplicação.')


router = APIRouter(dependencies=[Depends(autenticar)])


@router.get('/health', response_model=HealthOut, summary='Verificar API e modelo', description='Informa o provedor configurado e verifica se o modelo está acessível. A API permanece disponível para regras quando o modelo está fora do ar.')
def health(request: Request):
    bot = request.app.state.bot
    return {'status':'ok', 'provider':bot.config.provider, 'model':bot.config.model, 'model_available':bot.llm.disponivel()}


@router.post('/sessions', response_model=SessionOut, status_code=201, summary='Iniciar conversa', description='Cria memória e slots no servidor e devolve a saudação com as capacidades da Lia.')
def criar_sessao(request: Request):
    bot = request.app.state.bot
    with bot.lock:
        return bot.store.criar(bot.config.model)


@router.get('/models', response_model=list[ModelOut], summary='Listar modelos disponíveis')
def modelos(request: Request):
    return opcoes(request.app.state.bot.config)


@router.patch('/sessions/{session_id}/model', response_model=SessionOut,
              summary='Selecionar modelo da conversa')
def selecionar_modelo(session_id: str, dados: ModelIn, request: Request):
    bot = request.app.state.bot
    if dados.model not in {m['id'] for m in opcoes(bot.config)}:
        raise HTTPException(422, 'Selecione um dos modelos disponíveis na plataforma.')
    try:
        with bot.lock:
            return bot.store.selecionar_modelo(session_id, dados.model)
    except KeyError:
        raise HTTPException(404, 'Conversa não encontrada. Inicie uma nova conversa.')


@router.post('/chat', response_model=ChatOut, summary='Enviar mensagem', description='Delega ao orquestrador e devolve resposta, intenção, slots, sentimento e handoff. O estado não depende da tela.', responses={404:{'description':'Sessão inexistente'},503:{'description':'Modelo indisponível; estado preservado'}})
def chat(dados: ChatIn, request: Request):
    try:
        return request.app.state.bot.chat(dados.session_id, dados.message)
    except KeyError:
        raise HTTPException(404, 'Conversa não encontrada. Inicie uma nova conversa.')
    except ModeloIndisponivel as erro:
        raise HTTPException(503, str(erro))


@router.get('/sessions/{session_id}', response_model=SessionOut, summary='Consultar conversa', description='Retorna todo o histórico persistido, slots validados e o último raio-X, para qualquer lente.')
def obter_sessao(session_id: str, request: Request):
    bot = request.app.state.bot
    try:
        with bot.lock:
            return bot.store.obter(session_id)
    except KeyError:
        raise HTTPException(404, 'Conversa não encontrada. Inicie uma nova conversa.')


@router.get('/metrics', response_model=MetricsOut, summary='Consultar métricas', description='Calcula métricas sobre os turnos do log SQLite; sessões vazias não entram no denominador. Contenção exige encerramento sem handoff.')
def metrics(request: Request):
    return calcular_metricas(request.app.state.bot.store)


@router.delete('/sessions/{session_id}', status_code=204, summary='Apagar conversa', description='Apaga histórico, slots, reservas fictícias, feedback e eventos analíticos da sessão. Não há recuperação pela aplicação.')
def apagar(session_id: str, request: Request):
    bot = request.app.state.bot
    try:
        with bot.lock:
            bot.store.apagar(session_id)
    except KeyError:
        raise HTTPException(404, 'Conversa não encontrada.')
    return Response(status_code=204)


@router.post('/feedback', status_code=201, response_model=dict[str,str], summary='Avaliar conversa', description='Recebe uma nota inteira de 1 a 5. Uma nota por sessão; uma nova avaliação substitui a anterior.')
def feedback(dados: FeedbackIn, request: Request):
    bot = request.app.state.bot
    try:
        with bot.lock:
            bot.store.feedback(dados.session_id, dados.rating)
    except KeyError:
        raise HTTPException(404, 'Conversa não encontrada.')
    return {'message':'Avaliação registrada. Obrigada!'}


@router.get('/handoffs', response_model=list[HandoffOut], summary='Consultar fila humana', description='Disponibiliza dados coletados, intenção, relato e ações já tomadas para uma segunda lente.')
def handoffs(request: Request):
    return request.app.state.bot.store.handoffs()
