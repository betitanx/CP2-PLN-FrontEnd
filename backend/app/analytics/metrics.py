import json
from collections import Counter


def calcular_metricas(store):
    with store.conexao() as db:
        eventos = [json.loads(r[0]) for r in db.execute('SELECT payload FROM turns')]
        notas = [r[0] for r in db.execute('SELECT rating FROM feedback')]
        erros = db.execute('SELECT COUNT(*) FROM errors').fetchone()[0]
    # O denominador inclui sessões com pelo menos um turno concluído, inclusive ativas.
    sessoes = {e['session_id'] for e in eventos}
    handoffs = {e['session_id'] for e in eventos if e['handoff']}
    encerradas = {e['session_id'] for e in eventos if e['status'] == 'encerrada'} - handoffs
    falhas = [e for e in eventos if e['fallback']]
    total, turnos = len(sessoes), len(eventos)
    return {'total_conversas': total, 'total_turnos': turnos,
            'conversas_encerradas_sem_handoff': len(encerradas), 'conversas_com_handoff': len(handoffs),
            'turnos_fallback': len(falhas), 'taxa_contencao': len(encerradas) / total if total else 0,
            'taxa_fallback': len(falhas) / turnos if turnos else 0,
            'taxa_handoff': len(handoffs) / total if total else 0,
            'mensagens_por_conversa': turnos / total if total else 0,
            'latencia_media_ms': sum(e['latency_ms'] for e in eventos) / turnos if turnos else 0,
            'eventos_guardrail': sum(len(e['guardrail_events']) for e in eventos),
            'csat_medio': sum(notas) / len(notas) if notas else None, 'respostas_csat': len(notas),
            'fallback_por_intencao': dict(Counter(e['intent'] for e in falhas)), 'erros_modelo': erros}
