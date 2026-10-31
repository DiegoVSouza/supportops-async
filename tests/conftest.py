from pathlib import Path

import pytest

# These four tests drive the revalidation operation together with files that live in the ai-engineer-lab checkout
# (scripts/harness and shared/policies). Outside the lab they cannot run, so they are skipped with the reason printed
# by `pytest -rs`; inside the lab they run unchanged. The other tests in the module run everywhere.
_LAB = Path(__file__).resolve().parents[3]
_LAB_PRESENT = (_LAB / "shared/policies/groq-free-campaign.json").is_file() and (_LAB / "scripts/harness/live_free_account.py").is_file()
_LAB_TESTS = {
    "test_applied_migration_rechecks_without_reacquiring_campaign_lease",
    "test_authority_binds_exact_scope_without_opening_a_provider",
    "test_reentrant_check_rejects_changed_history_prefix",
    "test_reentrant_check_rejects_missing_or_invalid_audit",
}


def pytest_collection_modifyitems(config, items):
    if _LAB_PRESENT:
        return
    skip = pytest.mark.skip(
        reason="lab integration test: needs scripts/harness and shared/policies from the ai-engineer-lab checkout, absent here"
    )
    for item in items:
        if item.name in _LAB_TESTS:
            item.add_marker(skip)
