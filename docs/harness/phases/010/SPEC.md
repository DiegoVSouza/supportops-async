# SPEC — Preserve work during early SQS redelivery

The phase 009 audit found that Worker acknowledges a message when the PostgreSQL claim is still leased. After a worker dies and SQS visibility expires before its database lease, this can delete the only message before recovery is possible. Release 0.1.3 must defer the message instead. Public method signatures and task contracts remain compatible.

Acceptance: a red unit regression and real PostgreSQL/SQS kill/recovery scenario consume the message before lease expiry, preserve it, and finish after expiry without repeating the committed effect. Build a versioned wheel with origin commit, SHA-256 and isolated consumer evidence. Update P03/P05 consumers.
