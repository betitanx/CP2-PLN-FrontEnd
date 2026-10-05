"""Avalia históricos registrados no servidor; não substitui revisão humana."""
import argparse
import json
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description='Avaliar conversas pela API, com o modelo de cada sessão.')
    parser.add_argument('--entrada', type=Path, default=BASE.parent / 'docs/resultado_modelo_real.json')
    parser.add_argument('--saida', type=Path, default=BASE.parent / 'docs/avaliacao_qualidade.json')
    parser.add_argument('--url', default='http://localhost:8000')
    parser.add_argument('--limite', type=int, default=3)
    args = parser.parse_args()
    if args.limite < 1:
        parser.error('O limite deve ser positivo.')
    load_dotenv(BASE / '.env')
    if not os.getenv('API_KEY'):
        parser.error('Configure API_KEY no backend/.env.')
    casos = json.loads(args.entrada.read_text(encoding='utf-8'))['casos'][:args.limite]
    resultados = []
    with httpx.Client(base_url=args.url, headers={'X-API-Key': os.environ['API_KEY']}, timeout=90) as cliente:
        for caso in casos:
            r = cliente.post(f"/sessions/{caso['session_id']}/avaliacao")
            resultados.append({'caso': caso['caso'], 'status_http': r.status_code,
                               'avaliacao': r.json()})
            if not r.is_success:
                break
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps({'tipo': 'avaliacao_automatica', 'resultados': resultados},
                                     ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Avaliações registradas: {len(resultados)}. Arquivo: {args.saida}')
    if any(r['status_http'] != 200 for r in resultados):
        raise SystemExit('Avaliação interrompida: confira o erro registrado. Não houve repetição automática.')


if __name__ == '__main__':
    main()
