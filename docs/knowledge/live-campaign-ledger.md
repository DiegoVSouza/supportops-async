# Ledger local de workflows — P04

## Aprendizado

Uma chamada LLM pode ter sido cobrada mesmo se o worker cair antes de salvar a resposta. Grave a reserva antes do despacho, mantenha a reserva integral quando o uso ficar desconhecido e marque a tentativa como incerta para impedir repetição automática. Isso não promete entrega única nem cobrança única; o ledger contabiliza os limites planejados e não prova o estado de efeitos do workflow.

O SQLite local do P04 é append-only, serializa reservas concorrentes e separa cada campanha por ID. O lease de sistema operacional impede campanhas concorrentes. A retomada expõe somente IDs de campanha/caso/trial e uso, sem texto de tarefa, plano, resposta ou ferramenta.

## Limites atuais

O dispatcher ainda não existe e o lease ainda não foi ligado a uma execução live aprovada. A validação de serviço real continua pendente: a full gate desta fase passou nos testes, mas terminou `INCOMPLETE` porque PostgreSQL, LocalStack, Redis, Docker build e Terraform foram isolados. Quota, orçamento, revisão e preflight também estão pendentes; USD 0 não mudou.

## Resposta de entrevista (PT-BR)

Implementei reservas persistentes e contabilidade transacional para limitar chamadas de uma campanha P04, sem guardar conteúdo de workflows. Tentativas incertas ficam reservadas e não são repetidas automaticamente. Os testes offline passaram, mas a fase não habilita live: faltam aprovação de quota, dispatcher e validação do serviço real com Postgres, SQS e Redis.

## Interview answer (English)

I implemented durable reservations and transactional campaign accounting for P04 without storing workflow content. Uncertain attempts remain charged against the reservation and are not retried automatically. Offline tests pass, but this phase does not enable live execution: quota approval, dispatch, and the real Postgres/SQS/Redis service gate are still missing.
