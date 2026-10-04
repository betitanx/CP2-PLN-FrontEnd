# Evidências de verificação

Execução local em 04/10/2026 com Python 3.13 e as dependências fixadas nos arquivos de requisitos.

| Verificação | Resultado | Limite da evidência |
|---|---|---|
| Testes do backend | 31 passaram | Provedor externo substituído somente nos testes; inclui OPEN_ROUTER_KEY, falhas consecutivas de validação, preservação de relato e conteúdo nulo do modelo |
| Testes do frontend | 8 passaram | Erros HTTP, timeout, mensagem de cota do OpenRouter e AppTest com API indisponível e troca de modelo por HTTP |
| Seleção de modelo | Gemma 4 A4B e Nemotron 3 Super; preservação de histórico, isolamento entre sessões, persistência e modelo enviado ao provedor | Inferência substituída nos testes; não mede qualidade dos modelos |
| Avaliação T1–T8 e dez conversas | 18 conversas, 66 turnos, resultado_modelo_real.json; nenhuma falha de modelo | API HTTP real e Nemotron real quando o fluxo exige inferência; amostra dirigida |
| Dois processos em portas diferentes | FastAPI 8000 e Streamlit 8501 funcionando | Ambiente local de demonstração |
| T8 com interface real | Streamlit coletou nome/placa; Swagger enviou a data na mesma sessão; tela atualizada exibiu turno 4 com os três slots | Exercício determinístico; não testa qualidade do modelo |
| Painel de métricas | Valores obtidos da API e mostrados no Streamlit | Banco da interface separado do lote de 18; inclui conversas de verificação anteriores |
| Capturas | Chat, raio-X, métricas e Swagger em prints | Capturadas na largura disponível do navegador |

O backend emitiu um aviso de descontinuação no cliente de testes Starlette/HTTPX; os testes concluíram sem falhas. Não há aviso apresentado ao usuário na aplicação.

As capturas não são evidência de atendimento por pessoas reais. Todos os dados são fictícios. As capturas iniciais foram feitas antes da mudança do provedor. As capturas teste_agendamento.jpg e teste_handoff.jpg correspondem aos testes práticos posteriores, com a configuração atual. Foi usado OpenRouter com chave real em duas chamadas de verificação: Nemotron respondeu com intenção agendar em 850,22 ms; Gemma retornou HTTP 429 em 1.027,11 ms. Não foi instalado ou executado o Qwen nesta máquina, nem foi usada uma chave comercial da OpenAI. O lote real, o relatório e os nomes/RMs foram concluídos posteriormente; acesso dos professores ao repositório privado e vídeo com os integrantes continuam pendentes para o checkpoint. A comparação completa está em revisao_requisitos.md.

O catálogo público foi consultado em 04/10/2026: as duas opções têm preço zero e suporte a response_format. A chave estava no .env.example e foi transferida ao .env local, excluído da entrega. O resultado das duas chamadas autenticadas está em verificacao_modelos_reais.json. Não houve repetição automática do erro de cota.

A captura prints/modelos.jpg foi feita após a alteração: mostra as duas famílias no seletor. A seleção de Nemotron pela interface foi confirmada por GET /sessions na mesma sessão.

Testes práticos atuais: agendamento completo com placa inválida corrigida, interrupção por FAQ, retomada de horários, CSAT 5, nova sessão isolada, paráfrase interpretada pelo Nemotron (1.105,77 ms) e sentimento negativo com resumo humano exibido na fila. Erros HTTP 401/404/422 confirmados no serviço ativo. Detalhes em testes_praticos.md e resultado_testes_interface.json.
