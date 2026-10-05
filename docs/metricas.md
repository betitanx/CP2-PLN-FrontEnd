# Relatório de métricas da Oficina Roda Certa

**Avaliação em 04/10/2026 com API HTTP e OpenRouter reais**, usando `nvidia/nemotron-3-super-120b-a12b:free`. T1–T8 e dez conversas adicionais foram repetidos com datas brasileiras DD/MM/AAAA em banco SQLite isolado: 18 conversas e 66 turnos. Regras e FAQ respondem sem inferência; apenas linguagem fora das regras consulta o modelo. O retorno das métricas e os históricos fictícios estão em `resultado_modelo_real.json`.

| Indicador | Retorno observado |
|---|---|
| Conversas / turnos | 18 / 66 |
| Encerradas sem handoff | 9 |
| Conversas com handoff | 3 |
| Turnos em fallback | 7 |
| Taxa de contenção | 50,00% |
| Taxa de fallback | 10,61% |
| Taxa de handoff | 16,67% |
| Mensagens por conversa | 3,67 |
| Latência média de todos os turnos | 83,41 ms |
| Eventos de guardrail / erros de modelo | 3 / 0 |
| CSAT | Sem avaliações no lote |

**Leitura crítica.** Cinco fallbacks ocorreram com intenção desconhecida e dois com agendar, por dados inválidos. Seis conversas ficaram abertas; não devem ser tratadas como fracassos. Os oito cenários passaram pelas verificações previstas. As respostas de negócio permaneceram em português, usaram a base curada e preservaram dados válidos. A interpretação das entradas vagas manteve o fallback e a oferta humana. Isso valida os cenários da amostra, sem provar qualidade geral do modelo.

**Latência e custo.** A média de 83,41 ms mistura turnos determinísticos e turnos com inferência; não é a latência média do Nemotron. Uma chamada isolada de classificação real respondeu em 850,22 ms. Em um novo lote separado com Dots3-Note, 18 conversas e 66 turnos passaram, com zero erros e média geral de 118,81 ms; a classificação isolada pela API levou 1.376,03 ms. Os dois modelos atuais tinham preço zero no catálogo consultado. As amostras não constituem comparação A/B controlada de qualidade ou velocidade. Nenhuma troca para modelo pago ou repetição automática foi usada. O novo lote está em `resultado_dots.json`.

**Melhoria proposta.** Ampliar a FAQ para serviços adicionais somente após validação humana; medir pelo menos dez paráfrases por intenção, separar latência de regras e inferência e coletar CSAT. Esta é uma amostra acadêmica dirigida: não representa tráfego real, satisfação de usuários nem disponibilidade garantida do provedor. O T8 manual complementa as evidências da avaliação automatizada.

**Diferenciais verificados em outro banco.** Três conversas receberam notas fictícias de teste: contida 5/5, transferida 2/5 e em andamento 3/5, com uma avaliação em cada grupo. O serviço passou a cruzar CSAT com o resultado da conversa; esses dados não são satisfação real nem integram o lote de 18 conversas acima. Reiniciar a API preservou sessões, logs, feedback e fila. Duas avaliações reais por Nemotron foram salvas com notas e justificativas nos três critérios. Dots3-Note também gerou uma avaliação real válida de seis turnos, registrada em `resultado_dots.json`. Evidências e limites: `resultado_diferenciais.json` e `testes_praticos.md`.
