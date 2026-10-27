# Sistemas assíncronos duráveis

## Entrega, idempotência e recuperação

Redis Streams entrega mensagens ao menos uma vez por meio de consumer groups. Se um worker cair, outra instância pode reivindicar a mensagem depois do visibility timeout. O consumidor tolera duplicatas usando chave de idempotência e o ledger `(task_id, step)`. O P04 mantém um adapter SQS para ambientes AWS; o Compose local usa Redis persistente.

Isso não torna um efeito externo universalmente “exactly once”. Se o serviço externo aceitar uma chave idempotente, envie a mesma chave em cada retry. Sem suporte no destino, uma queda entre executar o efeito e salvar sua confirmação pode duplicá-lo.

O PostgreSQL mantém o lease da tarefa e Redis controla a posse temporária da mensagem. Workers longos renovam os dois. O Redis usa AOF no Compose para recuperar streams após reinício; os dados do produto continuam no PostgreSQL.

## Retry, backoff e DLQ

Falhas transitórias são tentadas novamente com atraso exponencial limitado. Falhas permanentes e tentativas esgotadas vão para uma dead-letter queue (DLQ), onde ficam para investigação e reprocessamento consciente. Retry sem limite pode ocupar workers e aumentar a carga durante uma indisponibilidade; um limite baixo demais pode descartar trabalho recuperável.

## Correlação de traces e falhas privadas

O P04 propaga somente `traceparent` W3C da requisição HTTP pela mensagem do broker, retry, redelivery e thread de execução do worker. Baggage e outros headers não são copiados. Novos erros persistidos e logs do worker usam categorias fixas, sem texto de exceção. Isso reduz vazamento acidental, mas não substitui revisão dos campos de domínio nem a política de retenção.

O contrato offline foi testado entre FastAPI, envelopes SQS/Redis e thread local do worker. O projeto ainda não configura SDK/exporter ou collector; entrega de traces a um backend permanece INCOMPLETE. O P04 também não possui fonte RAG própria ou protocolo de autorização de retrieval.

## Trace correlation and private failures

P04 propagates only W3C `traceparent` from the HTTP request through the broker message, retry, redelivery, and worker execution thread. It does not copy baggage or other headers. Newly persisted worker failures and CLI logs use fixed categories without exception text. This reduces accidental leakage but does not replace review of domain fields or retention policy.

The offline contract was tested across FastAPI, SQS/Redis envelopes, and the local worker thread. The project does not configure an SDK/exporter or collector, so delivery to a trace backend remains INCOMPLETE. P04 also lacks an owned RAG source and retrieval authorization protocol.

## Outbox e saga

Uma outbox grava a intenção de publicar um evento na mesma transação que altera o estado de domínio. Um publicador separado envia os eventos e marca os entregues. O envio pode duplicar se o processo cair entre publicar e marcar; consumidores continuam precisando deduplicar pelo `event_id`.

Uma saga coordena passos locais com compensações quando uma operação distribuída não cabe em uma transação. Compensar não apaga o histórico nem garante que um efeito externo nunca tenha sido observado.

## Visibility timeout, backpressure e filas

O visibility timeout precisa cobrir o processamento ou ser renovado por heartbeat. Muito curto causa duplicatas concorrentes; muito longo atrasa a recuperação de workers mortos. Backpressure limita concorrência e publicação para que a fila não cresça mais rápido do que os consumidores processam.

SQS oferece serviço gerenciado, DLQ e integração com IAM. Kafka mantém log ordenado por partição e favorece replay e consumidores independentes, mas exige decisões de partição, retenção e operação. Kafka não é automaticamente melhor para tarefas de suporte; ordenação e replay devem justificar sua complexidade.

## Evidência de serviço local — 2026-10-21

O gate executado contra PostgreSQL 17.11 e LocalStack 4.14.0 manteve uma etapa por 31,7 segundos, acima do lease de 30 segundos, sem permitir claim concorrente e com a tarefa persistida como concluída. A entrega duplicada criou um único registro de efeito; três tentativas falhas encaminharam uma mensagem à DLQ. O comando reproduzível e os resultados estão em `artifacts/evidence/phase-008-service-scenarios.txt`. A queda do worker após commit de efeito externo ainda não foi simulada contra esses serviços; por isso, recuperação completa de crash e semântica exactly-once permanecem INCOMPLETE.

## Respostas de entrevista / Interview answers

**EN — What does at-least-once delivery mean?**

The broker may redeliver a message when acknowledgment is lost or processing outlives its visibility lease. Consumers must be idempotent, and the system should record attempts and route exhausted work to a DLQ.

**PT — O que significa entrega ao menos uma vez?**

O broker pode entregar a mesma mensagem novamente se a confirmação se perder ou o processamento ultrapassar o lease de visibilidade. Consumidores precisam ser idempotentes; o sistema deve registrar tentativas e encaminhar o trabalho esgotado para uma DLQ.

**EN — Can a database checkpoint guarantee exactly-once external effects?**

No. A crash can happen after the external effect succeeds but before the checkpoint commits. Exactly-once behavior requires an idempotency key accepted by the destination or a transaction shared with it. The local effect ledger only proves exactly-once behavior for the fake effect in its own database transaction.

**PT — Um checkpoint no banco garante efeito externo exatamente uma vez?**

Não. O processo pode cair depois que o efeito externo acontece e antes do commit do checkpoint. É preciso uma chave idempotente aceita pelo destino ou uma transação compartilhada. O ledger local só demonstra efeito único para a simulação fake, dentro da própria transação.

**EN — When would you choose SQS over Kafka?**

I would choose SQS for independent task messages when managed delivery, visibility timeouts, and DLQs meet the needs. Kafka fits when partition ordering, retained event logs, and multiple replaying consumers justify operating a streaming platform.

**PT — Quando escolher SQS em vez de Kafka?**

Eu escolheria SQS para mensagens independentes quando entrega gerenciada, visibility timeout e DLQ atendem ao caso. Kafka faz mais sentido quando ordenação por partição, retenção de eventos e vários consumidores com replay justificam operar uma plataforma de streaming.

## 2026-10-22 — Phase 010 evidence supersedes earlier pending notes

A real PostgreSQL lease/SQS visibility flow now proves early redelivery deferral and recovery following worker termination after an effect commit. P04 0.1.3 full service gate includes long-step, duplicate delivery, retry-to-DLQ, and Terraform plan-only checks. Model quality/cost remain PENDING; external deployment remains outside local acceptance.

## 2026-10-23 — Redis Streams service verification

The Compose runtime now uses Redis Streams for task delivery, with AOF persistence, consumer-group reclaim after the visibility timeout, delayed retry, and a separate DLQ stream. The SQS adapter remains available for AWS. The phase 012 gate passed Redis broker recovery/retry/DLQ plus the existing PostgreSQL and LocalStack SQS scenarios; evidence is `artifacts/evidence/phase-012-full-gate.txt`. Redis transport does not change PostgreSQL task state or make arbitrary external effects exactly once.

## 2026-10-27 — Phase 017 isolated PostgreSQL/SQS recheck

The phase-016 source candidate (`0d427e3e9b509fec19450d52f45e35aab9bbed33`) passed the service scenario against a fresh, phase-owned PostgreSQL 17.11 and LocalStack 4.14.0 stack. The long task completed in 31.8 seconds without a competing lease claim and persisted its effect. Duplicate delivery led to one task claim/effect record. Retry exhaustion reached three attempts and exactly one DLQ message. The Compose mapping is fixed to loopback ports 15432 and 14566; inspect the file rather than assuming custom ports. All phase resources were removed and pre-existing Docker identities/states were preserved.

This scoped service evidence does not prove API-to-exporter trace delivery, RAG behavior, Docker image build, Terraform, provider quality, or promotion. Trace-export and RAG acceptance remain INCOMPLETE; human and independent review remain pending. Evidence: `artifacts/evidence/service-scenarios-017/report.md`.

## 2026-10-27 — Phase 018 safe full local gate

The full local gate passed on candidate `ee8c867b824b7727f547dd01b07275b179687add`: 70 tests passed, one Redis broker test skipped because no Redis service endpoint was configured, PostgreSQL/SQS scenarios passed, the image built, and Terraform init/validate plus LocalStack plan passed with 6 additions, zero changes, and zero destroys. No Terraform apply ran. `scripts/check_full.py` now requires a fresh evidence-owned pytest temp directory and refuses to clear an existing one; all three historical scratch database hashes remained unchanged.

The build updated the P04-local `supportops-async:local-check` tag from the prior image ID (recorded in the phase report) to the image for the current source candidate. This did not change any running container, network, or volume. Redis service-backed behavior, API trace exporter delivery, RAG, model quality, and human/independent/promotion review remain incomplete or pending. Evidence: `artifacts/evidence/full-gate-018/report.md`.

## 2026-10-27 — OTLP exporter lifecycle (phases 019–020)

The SDK exporter must support both a proxy/no-op global provider and an SDK provider installed by host instrumentation before FastAPI lifespan. Replacing an established global provider is rejected by the OTel API. For an existing SDK provider, attach a single exporter only when its `service.name` matches the process service name, and shut down only the exporter processor owned by this package. Validate the endpoint before either branch. A real synthetic API/worker Jaeger trace plus GET-only privacy check is required; offline tests cannot prove delivery. Preserve the phase-019 failed trace; phase 020 used a new task/trace. Neither is model-quality or promotion evidence.
