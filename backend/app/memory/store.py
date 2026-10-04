import json
import sqlite3
import uuid
from contextlib import contextmanager

SAUDACAO = 'Olá! Sou a Lia, assistente virtual da Oficina Roda Certa fictícia. Posso agendar uma avaliação, responder dúvidas da oficina ou encaminhar para um atendente. Use apenas dados fictícios. Como posso ajudar?'


class Store:
    def __init__(self, caminho):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho = caminho
        with self.conexao() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS turns (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS feedback (session_id TEXT PRIMARY KEY, rating INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS bookings (data TEXT, horario TEXT, session_id TEXT UNIQUE, PRIMARY KEY(data, horario));
                CREATE TABLE IF NOT EXISTS errors (id INTEGER PRIMARY KEY, session_id TEXT, timestamp TEXT, kind TEXT);
            ''')

    @contextmanager
    def conexao(self):
        db = sqlite3.connect(self.caminho, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def criar(self, model=None):
        sid = str(uuid.uuid4())
        s = {'model': model, 'session_id': sid, 'greeting': SAUDACAO,
             'history': [{'role': 'assistant', 'content': SAUDACAO}],
             'slots': dict.fromkeys(['nome', 'placa', 'data', 'horario']),
             'status': 'ativa', 'handoff': {'active': False, 'reason': None, 'summary': None},
             'turn': 0, 'last_turn': None, 'fluxo': False, 'falhas': 0,
             'oferta_humano': False, 'sugeridos': [], 'acoes': []}
        with self.conexao() as db:
            db.execute('INSERT INTO sessions VALUES (?,?)', (sid, json.dumps(s, ensure_ascii=False)))
        return s

    def obter(self, sid):
        with self.conexao() as db:
            row = db.execute('SELECT payload FROM sessions WHERE id=?', (sid,)).fetchone()
        if not row:
            raise KeyError(sid)
        return json.loads(row[0])

    def selecionar_modelo(self, sid, model):
        s = self.obter(sid)
        s['model'] = model
        with self.conexao() as db:
            db.execute('UPDATE sessions SET payload=? WHERE id=?',
                       (json.dumps(s, ensure_ascii=False), sid))
        return s

    def salvar(self, s, evento, reserva=None):
        with self.conexao() as db:
            if reserva:
                db.execute('INSERT INTO bookings VALUES (?,?,?)', (*reserva, s['session_id']))
            db.execute('UPDATE sessions SET payload=? WHERE id=?', (json.dumps(s, ensure_ascii=False), s['session_id']))
            db.execute('INSERT INTO turns(session_id,payload) VALUES (?,?)', (s['session_id'], json.dumps(evento, ensure_ascii=False)))

    def ocupados(self, data):
        with self.conexao() as db:
            return [r[0] for r in db.execute('SELECT horario FROM bookings WHERE data=?', (data,))]

    def apagar(self, sid):
        self.obter(sid)
        with self.conexao() as db:
            for tabela in ['turns', 'feedback', 'bookings', 'errors']:
                db.execute(f'DELETE FROM {tabela} WHERE session_id=?', (sid,))
            db.execute('DELETE FROM sessions WHERE id=?', (sid,))

    def feedback(self, sid, rating):
        self.obter(sid)
        with self.conexao() as db:
            db.execute('INSERT INTO feedback VALUES (?,?) ON CONFLICT(session_id) DO UPDATE SET rating=excluded.rating', (sid, rating))

    def erro(self, sid, timestamp):
        with self.conexao() as db:
            db.execute('INSERT INTO errors(session_id,timestamp,kind) VALUES (?,?,?)', (sid, timestamp, 'modelo_indisponivel'))

    def handoffs(self):
        with self.conexao() as db:
            sessoes = [json.loads(r[0]) for r in db.execute('SELECT payload FROM sessions')]
        return [{'session_id': s['session_id'], 'handoff': s['handoff']} for s in sessoes if s['handoff']['active']]
