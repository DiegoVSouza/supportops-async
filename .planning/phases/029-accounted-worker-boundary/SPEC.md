# Accounted API worker boundary

Connect the real Worker callable contract to an injected fixture session using the shared accounted envelope. Persist each operation/step reservation before dispatch, validate receipt/usage/model/output, and treat all uncertainty as permanent so queue retries cannot replay provider work. Verify through the real FastAPI/SQLite/broker/Worker path, duplicates and cancellation. Live activation/funding and service export remain separate pending gates.
