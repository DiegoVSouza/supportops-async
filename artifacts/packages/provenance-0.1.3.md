# P04 local wheel 0.1.3

Source commit: ef1fe4398d30a91d471ef6ddab226160050c5eaf

SHA-256: b9e0bc47793c1cebb29471db087084c52495ab20d6ee5debabca95d1d42156f8

Dependency-lock SHA-256: 7db6b099269f86aca84d2b811e961a218e0d9bfd6d48cc2adca118de00eddbc3

Build, isolated install and consumer: artifacts/evidence/phase-010-wheel-{build,install,consumer}.txt; all exit 0. The consumer loads package/migrations outside the source checkout with Python -I -S. The source full gate includes early redelivery and actual PostgreSQL/SQS crash recovery. No publication.
