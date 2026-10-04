# Comparação entre o enunciado e a implementação

Revisão em 04/10/2026 do documento CP Integrado FrontEnd PLN Bot como Serviço. Foram inspecionados código, configuração, testes e entregáveis. **O projeto implementa a estrutura exigida, mas ainda não reúne todas as evidências necessárias para entregar o checkpoint.** A avaliação real T1–T8 mais dez conversas foi concluída com Nemotron. O repositório privado está em betitanx/CP2-PLN-FrontEnd; o vídeo continua pendente.

## Correções feitas nesta revisão

1. O OpenRouter lê exclusivamente `OPEN_ROUTER_KEY`, com alteração no `.env.example`, README, mensagens de erro e testes. `LLM_API_KEY` permanece somente para o adaptador opcional de outro provedor; não substitui a chave do OpenRouter. Posteriormente, a chave encontrada no exemplo foi transferida ao .env local e excluída da entrega.
2. Duas falhas consecutivas na validação dos slots ou na confirmação também oferecem atendimento humano. Os dados válidos permanecem na sessão. Essas falhas passam a ser contabilizadas como fallback no log.
3. Mensagens após o handoff preservam o relato original e acrescentam o complemento mais recente. O histórico completo conserva os demais complementos.
4. Conteúdo nulo ou de tipo inválido retornado pelo modelo gera 503, preservando o estado, em vez de escapar como erro interno.

Verificação após as alterações: **31 testes do backend e 8 do frontend passaram, totalizando 39**. O lote T1–T8 mais dez conversas foi executado com API HTTP e Nemotron reais: 18 conversas, 66 turnos, sete fallbacks e nenhum erro de modelo. O relatório de métricas foi atualizado; resultado_modelo_real.json contém históricos fictícios e estados finais.

## Requisitos obrigatórios

“Implementado” significa que o código e a documentação foram conferidos; não significa que a demonstração com modelo real esteja concluída. Os caminhos abaixo são relativos à pasta do projeto.

| Requisito | O que foi encontrado | Situação e pendência |
|---|---|---|
| Caso de negócio, seção 3 | Oficina fictícia; fluxo com nome, placa, data e horário; seis FAQ; handoff por reclamação, sensibilidade ou pedido explícito | Implementado. Nenhum bot anterior ou template da Aula 2 foi fornecido para comparar fidelidade |
| Separação, seção 4 | Dois projetos, dois requirements e dois processos; frontend usa somente HTTP; URL configurável; estado no SQLite; rotas delegam ao orquestrador | Implementado e integração observada. Instalação em duas máquinas/ambientes limpos não foi repetida |
| Contrato, seção 5.1 | Cinco rotas obrigatórias e cinco opcionais; Pydantic; sucesso 200/201; erros 404/422/503; autenticação 401 | Implementado e testado. /health verifica chave e catálogo, não garante inferência ou disponibilidade de cota |
| R1 Design conversacional | docs/ficha_do_bot.md; persona Lia, limites, saudação, caminho feliz, fallback e resumo humano | Implementado. Cenários previstos passaram com Nemotron; não é garantia universal de estabilidade |
| R2 System prompt | backend/prompts/system_prompt.md com cinco camadas, carregado no servidor | Implementado. T1–T8 executados no serviço real; arquivo ainda precisa ser publicado no repositório |
| R3 Memória | Histórico persistido por sessão; janela de oito pares; slots e horários no contexto; T3/T8 e reinício do Store testados | Implementado. T8 foi observado no Streamlit e Swagger; T3 recupera horários por código. A retenção do histórico pelo LLM real ainda precisa ser exercitada |
| R4 Estado | Quatro slots, validação sintática de nome/placa, calendário e horários; estado exposto pela API | Implementado e testado. Não comprova identidade nem agenda real, conforme o caráter fictício do caso |
| R5 Regra × LLM | Agenda determinística JSON/SQLite; FAQ sem RAG; LLM para paráfrases, intenção e saudações; decisões justificadas no README | Implementado. Integração real observada; lote dirigido passou. Testes unitários continuam isolando o provedor |
| R6 Guardrails, fallback e handoff | Guardrails em código, log de eventos, oferta após duas falhas, resumo estruturado; duas correções nesta revisão | Implementado e testado nos cenários previstos. Regex não comprova resistência universal a ataques |
| R7 NLU e sentimento | Intenções por regras/LLM; sentimento léxico; frustração antecipa acolhimento e transferência | Implementado. Escore é heurístico; interpretação real observada em chamada de classificação; cobertura geral de paráfrases não medida |
| R8 Analytics | Eventos SQLite por turno; quatro métricas obrigatórias; contadores de erro/guardrails e CSAT | Cálculo implementado. Relatório atualizado com API e modelo reais, sem confundir latência geral com inferência |
| F1 Separação de projetos | Módulos e configurações independentes; sem import do backend no frontend | Implementado e conferido. Backend e frontend de verificação rodaram em portas diferentes |
| F2 API FastAPI | APIRouter, modelos de entrada/saída, X-API-Key, Swagger descritivo e captura | Implementado e testado |
| F3 Consumo e erros | services/api_client.py concentra HTTP; timeout e mensagens amigáveis; AppTest sem API não mostra traceback | Implementado e testado. A chave OpenRouter permanece somente no backend |
| F4 Interface | Chat, raio-X, métricas, nova conversa; capturas em docs/prints | Implementado e observado. Vídeo das áreas e dos oito testes falta |
| F5 Reprodutibilidade | README com dois ambientes/comandos; arquivos de requisitos e .env.example | Documentado. Execução local real concluída; instalação em máquina limpa ainda não repetida |
| Modelo, seção 5.4 | OpenRouter gratuito como padrão; acesso isolado; custos e limites documentados; Ollama opcional | Parcial. Gemma 4 A4B e Nemotron 3 Super estão disponíveis no seletor, com escolha persistida por sessão. O padrão é Gemma; a avaliação deve registrar a opção escolhida. Nemotron classificou agendamento em chamada real e concluiu o lote de 18 conversas; média geral 86,05 ms. Gemma retornou 429 e não foi comparado |
| Sem RAG, seção 5.5 | FAQ curada atrás de buscar_faq, sem embeddings ou banco vetorial | Atendido |
| Testes obrigatórios, seção 6 | T1–T8 automatizados; lote de 18 conversas; prova manual de T8 entre Streamlit e Swagger | Parcial. Testes automatizados isolam o modelo. T1–T8 passaram com serviço real. Falta gravar os oito cenários com os integrantes |

O denominador das métricas considera sessões com pelo menos um turno concluído; sessões vazias não são conversas iniciadas efetivamente. Sessões ativas entram no denominador e não contam como contidas. Erros 503 são contabilizados separadamente. Esses critérios estão explícitos no README e precisam ser mantidos na leitura do relatório.

## Entregáveis acadêmicos

| Entregável | Situação |
|---|---|
| 7.1 GitHub | Repositório privado betitanx/CP2-PLN-FrontEnd; código também disponível no ZIP. Acesso aos professores deve ser concedido |
| 7.2 README | Caso, arquitetura, API, tecnologias, execução, decisões, limitações e uso de IA presentes; nomes, RMs, divisão prevista de revisão/apresentação e justificativa do modelo preenchidos; divisão não atribui autoria passada |
| 7.3 Ficha do bot | Presente, com o conteúdo exigido; formato exato do template da Aula 2 não pôde ser comparado porque o template não foi fornecido |
| 7.4 Relatório de métricas | Atualizado com o lote real: resultados, insight e limites documentados. Sem CSAT no lote e sem comparação entre os dois modelos |
| 7.5 Vídeo até cinco minutos | Roteiro presente. Vídeo, participação de todos e link não listado pendentes |

## Diferenciais

SQLite, exclusão de sessão, feedback CSAT e fila de handoffs estão implementados. O log analítico não armazena falas nem slots pessoais. A fila é uma área da mesma aplicação, não uma segunda aplicação independente. CSAT é uma média geral; cruzamento entre CSAT e contenção não está implementado. Streaming, sumarização, function calling, LLM-as-judge e comparação A/B também não estão implementados. Esses itens são opcionais e não são pendências dos requisitos mínimos.

## O que falta fazer antes de entregar

1. Concluído: configuração local, chave fora dos exemplos e autenticação entre projetos.
2. Concluído: seletor por sessão, com Gemma 4 A4B e Nemotron 3 Super. Gemma retornou 429; Nemotron foi usado na avaliação.
3. Concluído: T1–T8 e dez conversas por HTTP, com modelo real quando necessário, em banco separado. Verificação prática da interface documentada em testes_praticos.md; o vídeo continua pendente.
4. Concluído: resultado_modelo_real.json, relatório de métricas e justificativa empírica do modelo atualizados.
5. Concluído: nomes, RMs e divisão prevista de revisão/apresentação; autoria passada não foi inventada.
6. Repositório privado preparado em betitanx/CP2-PLN-FrontEnd, sem .env ou segredos; conceder acesso aos professores antes de entregar.
7. Gravar o vídeo no roteiro exigido, com todos os integrantes, e disponibilizar o link não listado junto ao repositório.

Não é possível afirmar uma nota nem marcar a entrega como completa apenas com os testes automatizados. As principais pendências são de validação do modelo e evidências acadêmicas, e não da separação entre frontend e backend.
