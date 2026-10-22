# Sistemas assíncronos duráveis

## Entrega, idempotência e recuperação

Filas como SQS normalmente oferecem entrega ao menos uma vez. Uma mensagem pode reaparecer quando o worker falha antes do ACK ou quando expira o visibility timeout. O consumidor deve tolerar duplicatas. Neste projeto, a tarefa usa uma chave de idempotência e cada efeito simulado usa `(task_id, step)`. O ledger do efeito e o checkpoint são gravados na mesma transação local.

Isso não torna um efeito externo universalmente “exactly once”. Se o serviço externo aceitar uma chave idempotente, envie a mesma chave em cada retry. Sem suporte no destino, uma queda entre executar o efeito e salvar sua confirmação pode duplicá-lo.

O worker mantém um lease para que uma tarefa `running` seja retomada depois que a posse expira. O SQS controla a invisibilidade da mensagem; workers longos renovam a visibilidade. O checkpoint reduz trabalho repetido e a chave do efeito impede repetir a simulação fake.

## Retry, backoff e DLQ

Falhas transitórias são tentadas novamente com atraso exponencial limitado. Falhas permanentes e tentativas esgotadas vão para uma dead-letter queue (DLQ), onde ficam para investigação e reprocessamento consciente. Retry sem limite pode ocupar workers e aumentar a carga durante uma indisponibilidade; um limite baixo demais pode descartar trabalho recuperável.

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
