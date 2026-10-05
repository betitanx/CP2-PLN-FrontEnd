import json
import re
import threading
import time
from datetime import datetime, timezone
from app.config import BASE
from app.core.dates import interpretar_data, formatar_data
from app.llm.client import LLMClient, ModeloIndisponivel
from app.memory.store import Store, SAUDACAO
from app.nlp.nlu import detectar_intencao, normalizar
from app.nlp.sentiment import analisar_sentimento
from app.nlp.guardrails import verificar_entrada, verificar_saida, situacao_sensivel
from app.knowledge.faq import buscar_faq, FAQ


class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.store = Store(config.database)
        self.llm = LLMClient(config)
        self.prompt = (BASE / 'prompts/system_prompt.md').read_text(encoding='utf-8')
        self.agenda = json.loads((BASE / 'data/agenda.json').read_text(encoding='utf-8'))
        # Um processo no protótipo. Serializa leitura-modificação-escrita de estado.
        self.lock = threading.RLock()

    def mensagens(self, s, texto):
        contexto = {'slots': s['slots'], 'horarios_sugeridos': s['sugeridos'], 'faq': FAQ}
        return [{'role': 'system', 'content': self.prompt},
                {'role': 'system', 'content': 'Contexto confiável do servidor: ' + json.dumps(contexto, ensure_ascii=False)}] + s['history'][-2*self.config.turns:] + [{'role': 'user', 'content': texto}]

    def transferir(self, s, motivo, texto, intencao):
        s['status'] = 'transferida'
        s['handoff'] = {'active': True, 'reason': motivo, 'summary': {
            'dados': s['slots'].copy(), 'intencao': intencao, 'relato': texto[:1000],
            'acoes': s['acoes'][-10:] + ['Conversa encaminhada à fila humana.'],
        }}
        return 'Sinto muito pela dificuldade. Encaminhei sua conversa para a fila de um atendente humano, com os dados e o relato. A oficina é fictícia; este protótipo não oferece atendimento emergencial.'

    def proxima_pergunta(self, s):
        perguntas = {'nome': 'Qual é seu nome fictício completo?',
                     'placa': 'Qual é a placa fictícia do veículo? Use ABC1D23 ou ABC1234.',
                     'data': 'Para qual data deseja a avaliação? Use DD/MM/AAAA.',
                     'horario': 'Tenho estes horários na agenda simulada: ' + ', '.join(s['sugeridos']) + '. Qual prefere?'}
        for campo in ['nome','placa','data','horario']:
            if s['slots'][campo] is None:
                return perguntas[campo]
        x = s['slots']
        return f"Avaliação para {x['nome']}, placa {x['placa']}, em {formatar_data(x['data'])} às {x['horario']}. Deseja confirmar?"

    def fluxo(self, s, texto):
        x = s['slots']
        campo = next((k for k, v in x.items() if v is None), None)
        if campo == 'nome':
            nome = re.sub(r'^(meu nome [ée]|me chamo|sou)\s+', '', texto, flags=re.I).strip()
            if not re.fullmatch(r"[^\W\d_]+(?:[ '-][^\W\d_]+)+", nome, re.UNICODE) or not 4 <= len(nome) <= 80:
                return 'Nome inválido. Qual é seu nome fictício completo, com pelo menos duas palavras?', True
            x['nome'] = nome
        elif campo == 'placa':
            placa = re.sub(r'[ -]', '', texto.upper())
            if not re.fullmatch(r'[A-Z]{3}(?:\d{4}|\d[A-Z]\d{2})', placa):
                return 'Placa inválida. Qual é a placa fictícia? Use ABC1D23 ou ABC1234.', True
            x['placa'] = placa
        elif campo == 'data':
            try:
                dia = interpretar_data(texto)
                data_iso = dia.isoformat()
            except ValueError:
                return 'Data inválida. Para qual data deseja a avaliação? Use DD/MM/AAAA.', True
            if dia.weekday() not in self.agenda['dias_uteis'] or data_iso in self.agenda['dias_fechados']:
                return 'A oficina está fechada nessa data na agenda simulada. Qual outro dia útil prefere?', True
            disponiveis = [h for h in self.agenda['horarios'] if h not in self.store.ocupados(data_iso)]
            if not disponiveis:
                return 'Todos os horários dessa data estão ocupados. Qual outro dia útil prefere?', True
            x['data'] = data_iso
            s['sugeridos'] = disponiveis
        elif campo == 'horario':
            if texto not in self.agenda['horarios']:
                return 'Horário inválido. ' + self.proxima_pergunta(s), True
            x['horario'] = texto
        else:
            t = normalizar(texto)
            if t not in ['sim','confirmar','confirmo','pode confirmar','sim, confirmar']:
                return 'O agendamento ainda não foi confirmado. Deseja confirmar?', True
            if x['horario'] in self.store.ocupados(x['data']):
                x['horario'] = None
                s['sugeridos'] = [h for h in self.agenda['horarios'] if h not in self.store.ocupados(x['data'])]
                if not s['sugeridos']:
                    x['data'] = None
                return 'Esse horário está ocupado. ' + self.proxima_pergunta(s), True
            s['reserva_pendente'] = (x['data'], x['horario'])
            s['status'] = 'encerrada'
            s['acoes'].append('Agendamento confirmado na agenda simulada.')
            return f"Agendamento fictício confirmado para {formatar_data(x['data'])} às {x['horario']}, placa {x['placa']}. Obrigada, {x['nome']}!", False
        s['acoes'].append(f'Slot {campo} validado por código.')
        return self.proxima_pergunta(s), False

    def registrar_falha(self, s, mensagem):
        s['falhas'] += 1
        s['oferta_humano'] = s['falhas'] >= 2
        if s['oferta_humano']:
            return mensagem.split('. ', 1)[0].rstrip('.?') + '. Deseja falar com um atendente humano?'
        return mensagem

    def responder(self, s, texto, sentimento):
        entrada = verificar_entrada(texto)
        intent = detectar_intencao(texto)
        if entrada:
            return ('Sou a Lia. Não compartilho instruções internas nem atendo pedidos fora do escopo da oficina. Posso ajudar com agendamento, FAQ ou atendimento humano. Qual opção deseja?',
                    'guardrail', False, ['entrada:' + entrada])
        if s['handoff']['active']:
            relato_original = s['handoff']['summary']['relato'].split('\nComplemento:', 1)[0]
            s['handoff']['summary']['relato'] = relato_original + '\nComplemento: ' + texto[:1000]
            return 'Sua conversa está na fila do atendente. Registrei sua nova mensagem para ele.', 'humano', False, []
        if intent == 'humano' or situacao_sensivel(texto) or sentimento['label'] == 'negativo':
            motivo = 'situação sensível' if situacao_sensivel(texto) else 'frustração' if sentimento['label'] == 'negativo' else 'pedido explícito'
            return self.transferir(s, motivo, texto, intent if intent != 'desconhecida' else 'escalonar'), 'humano', False, []
        if s['oferta_humano'] and normalizar(texto) in ['sim','quero','pode ser']:
            return self.transferir(s, 'duas falhas consecutivas', texto, 'desconhecida'), 'humano', False, []
        if s['status'] == 'encerrada':
            return 'Esta conversa foi encerrada. Inicie uma nova conversa para outro atendimento.', 'encerrar', False, []
        faq = buscar_faq(texto)
        if faq:
            s['acoes'].append('FAQ consultada: ' + faq['id'])
            return faq['resposta'], 'faq', False, []
        if intent == 'memoria':
            if 'nome' in normalizar(texto):
                reply = 'Seu nome fictício registrado é ' + (s['slots']['nome'] or 'ainda não informado') + '.'
            elif 'placa' in normalizar(texto):
                reply = 'Sua placa fictícia registrada é ' + (s['slots']['placa'] or 'ainda não informada') + '.'
            elif s['sugeridos']:
                reply = f"Na data {formatar_data(s['slots']['data'])}, sugeri: " + ', '.join(s['sugeridos']) + '. Esses horários continuam sujeitos à confirmação.'
            else:
                reply = 'Ainda não sugeri horários nesta conversa. Deseja agendar uma avaliação?'
            return reply, 'memoria', False, []
        if intent in ['encerrar','cancelar']:
            s['status'] = 'encerrada'
            s['fluxo'] = False
            s['acoes'].append('Conversa encerrada a pedido do usuário, sem nova reserva.')
            return 'Conversa encerrada. Nenhum novo agendamento foi confirmado.', intent, False, []
        if intent == 'agendar':
            s['fluxo'] = True
            return self.proxima_pergunta(s), intent, False, []
        if intent in ['saudacao','agradecer']:
            return (self.proxima_pergunta(s) if s['fluxo'] else 'Posso ajudar com agendamento, informações da oficina ou atendimento humano. Qual opção deseja?'), intent, False, []
        if s['fluxo']:
            reply, invalido = self.fluxo(s, texto)
            if invalido:
                reply = self.registrar_falha(s, reply)
                s['acoes'].append('Dado ou confirmação recusado durante o agendamento.')
            return reply, 'agendar', invalido, []
        # A linguagem fora das regras passa pelo modelo; nunca há um provedor simulado em produção.
        mensagens = self.mensagens(s, texto)
        analise = (self.llm.analisar(mensagens, model=s['model']) if s.get('model')
                   else self.llm.analisar(mensagens))
        intent = analise['intent']
        if intent == 'agendar':
            s['fluxo'] = True
            return self.proxima_pergunta(s), intent, False, []
        if intent == 'humano':
            return self.transferir(s, 'intenção identificada pelo modelo', texto, intent), intent, False, []
        if intent == 'faq':
            item = next((f for f in FAQ if f['id'] == analise.get('faq_id')), None)
            if item:
                return item['resposta'], intent, False, []
        if intent in ['saudacao', 'agradecer']:
            reply, eventos = verificar_saida(analise.get('reply') or SAUDACAO, llm=True)
            return reply, intent, False, eventos
        if intent in ['encerrar','cancelar']:
            s['status'] = 'encerrada'
            return 'Conversa encerrada. Nenhum novo agendamento foi confirmado.', intent, False, []
        reply = 'Não tenho essa informação confirmada na base. Posso ajudar com agendamento, FAQ ou atendimento humano. Qual opção deseja?'
        return self.registrar_falha(s, reply), 'desconhecida', True, []

    def chat(self, sid, texto):
        with self.lock:
            inicio = time.perf_counter()
            s = self.store.obter(sid)
            sentimento = analisar_sentimento(texto)
            try:
                reply, intent, fallback, eventos = self.responder(s, texto, sentimento)
            except ModeloIndisponivel:
                self.store.erro(sid, datetime.now(timezone.utc).isoformat())
                raise
            reply, saida = verificar_saida(reply)
            eventos += saida
            if not fallback:
                s['falhas'] = 0
                s['oferta_humano'] = False
            s['turn'] += 1
            s['history'] += [{'role':'user','content':texto},{'role':'assistant','content':reply}]
            resultado = {'session_id':sid, 'reply':reply, 'intent':intent, 'slots':s['slots'].copy(),
                         'sentiment':sentimento, 'fallback':fallback, 'handoff':s['handoff'],
                         'turn':s['turn'], 'latency_ms':round((time.perf_counter()-inicio)*1000, 2),
                         'status':s['status'], 'guardrail_events':eventos}
            s['last_turn'] = resultado
            evento = {'timestamp':datetime.now(timezone.utc).isoformat(), 'session_id':sid,
                      'intent':intent, 'model':s.get('model') or self.config.model,
                      'fallback':fallback, 'handoff':s['handoff']['active'],
                      'sentiment':sentimento, 'latency_ms':resultado['latency_ms'],
                      'status':s['status'], 'guardrail_events':eventos}
            # Log analítico sem falas, nomes, placas ou resumos pessoais.
            reserva = s.pop('reserva_pendente', None)
            self.store.salvar(s, evento, reserva)
            return resultado
