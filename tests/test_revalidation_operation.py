import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from scripts.revalidation_operation import (
    CAPS, CASE, CAMPAIGN, RESERVATION, LazySession, OperationBlocked, execute, live_preconditions,
    owner_allocation, reserve, verify_authority, write_once, INVOCATION,
)
from scripts.revalidation_operation import require_applied_migration_under_campaign_lease


class RevalidationOperationTests(unittest.TestCase):
    def test_applied_migration_rechecks_without_reacquiring_campaign_lease(self):
        import scripts.revalidation_operation as operation
        sys.path.insert(0, str(operation.LAB / "scripts/harness"))
        from live_free_account import machine_lease
        with machine_lease(operation.LAB / ".runtime/llm-live-readiness/campaign.lock"):
            self.assertIsNone(require_applied_migration_under_campaign_lease(operation.LAB))

    def test_reentrant_check_rejects_missing_or_invalid_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(OperationBlocked, "root_migration_unverified"):
                require_applied_migration_under_campaign_lease(Path(directory))

    def test_reentrant_check_rejects_changed_history_prefix(self):
        import scripts.revalidation_operation as operation
        sys.path.insert(0, str(operation.LAB / "scripts/harness"))
        import migrate_p01_p04_revalidation as migration
        with patch.object(migration, "verify_prefixes", side_effect=migration.MigrationBlocked("changed")):
            with self.assertRaisesRegex(OperationBlocked, "root_migration_unverified"):
                require_applied_migration_under_campaign_lease(operation.LAB)

    def test_owner_scope_and_paid_budget_are_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            value = {"project":"p04","execution_enabled":True,"synthetic_only":True,
                     "authorized_paid_spend_usd":"0.00","approved_campaigns":[CAMPAIGN],
                     "allocations":{CAMPAIGN:{"stage":"operation","case_ids":[CASE],
                                  "trials_per_case":1,"max_trials":1}}}
            (root / "evals/live-execution.json").write_text(json.dumps(value),encoding="utf-8")
            self.assertEqual(owner_allocation(root)["allocations"][CAMPAIGN]["case_ids"],[CASE])
            value["allocations"][CAMPAIGN]["max_trials"] = 2
            (root / "evals/live-execution.json").write_text(json.dumps(value),encoding="utf-8")
            with self.assertRaises(OperationBlocked): owner_allocation(root)

    def test_finite_reservation_preserves_unknown_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.sqlite"
            ledger = reserve(path)
            totals = ledger.totals()
            self.assertEqual(totals["requests"],3)
            self.assertEqual(totals["input_tokens"],12288)
            self.assertEqual(totals["output_tokens"],1536)
            self.assertEqual(totals["estimated_cost_usd"],RESERVATION["estimated_cost_usd"])
            with self.assertRaises((OperationBlocked,CampaignBlocked)): reserve(path)
            self.assertEqual(len(ledger.reserved_trials()),1)
            self.assertEqual(CAPS["requests"],9)

    def test_unhandled_failure_keeps_full_logical_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.sqlite"
            ledger = reserve(path)
            ledger.complete(case_id=CASE,trial=1,input_tokens=None,output_tokens=None,
                            actual_cost_usd=None,outcome="incomplete",error_class="unknown")
            totals=ledger.totals()
            self.assertEqual(totals["requests"],3)
            self.assertEqual(totals["input_tokens"],12288)
            self.assertEqual(totals["output_tokens"],1536)
            self.assertEqual(ledger.reserved_trials()[-1]["outcome"],"incomplete")

    def test_single_use_marker_is_create_only(self):
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/"invocation.json"
            write_once(marker,{"campaign":CAMPAIGN,"single_invocation":True})
            with self.assertRaises(OperationBlocked): write_once(marker,{"campaign":"other"})
            self.assertEqual(json.loads(marker.read_text())["campaign"],CAMPAIGN)

    def test_missing_credentials_stop_without_values_or_provider_access(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("scripts.revalidation_operation.LAB",Path(directory)), \
             patch.dict(os.environ,{},clear=True):
            result=live_preconditions()
        self.assertEqual(result["status"],"BLOCKED_PRECONDITION")
        self.assertEqual(result["reason"],"root_credentials_missing")
        self.assertFalse(result["provider_accessed"])
        self.assertFalse(result["values_exposed"])
        self.assertEqual(result["generation_calls"],0)

    def test_root_env_credential_is_accepted_without_process_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root / ".env").write_text("GROQ_API_KEY=root-secret\n",encoding="utf-8")
            with patch("scripts.revalidation_operation.LAB",root), patch.dict(os.environ,{},clear=True):
                self.assertIsNone(live_preconditions())

    def test_process_only_credential_stops_with_sanitized_source_report(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("scripts.revalidation_operation.LAB",Path(directory)), \
             patch.dict(os.environ,{"GROQ_API_KEY":"process-secret"},clear=True):
            result=live_preconditions()
        self.assertEqual(result["reason"],"root_credentials_missing")
        self.assertEqual(result["process_slots"],["GROQ_API_KEY"])
        self.assertEqual(result["provider_root_env_slots"],[])
        self.assertNotIn("process-secret",repr(result))

    def test_lazy_session_binds_exact_new_campaign_on_both_phases(self):
        class FakeSession:
            def __init__(self): self.seen=[]
            def preview(self,envelope): self.seen.append(("preview",envelope["campaign_id"]))
            def complete(self,envelope): self.seen.append(("complete",envelope["campaign_id"]))
        session=FakeSession()
        lazy=LazySession(lambda:session)
        lazy.preview({"campaign_id":"fixture-worker-v1"})
        lazy.complete({"campaign_id":"fixture-worker-v1"})
        self.assertEqual(session.seen,[("preview",CAMPAIGN),("complete",CAMPAIGN)])

    def test_execute_blocks_missing_keys_before_marker_or_provider(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("scripts.revalidation_operation.LAB",Path(directory)), \
             patch.dict(os.environ,{"LLM_MODE":"live"},clear=True), \
             patch("scripts.revalidation_operation.validate",return_value={}), \
             patch("scripts.revalidation_operation.verify_authority"):
            self.assertEqual(execute(),2)
        self.assertFalse((Path(__import__("scripts.revalidation_operation",fromlist=["PROJECT"]).PROJECT)/INVOCATION).exists())

    def test_authority_binds_exact_scope_without_opening_a_provider(self):
        calls=[]
        class FakeAccount:
            def __init__(self, root, policy):
                calls.append(("init",root,policy["model"]))
            def _history(self):
                calls.append(("history",))
                return []
            def _reviewed_revalidation(self,*args):
                calls.append(("scope",*args[1:]))
        fake=types.ModuleType("live_free_account")
        fake.SharedAccount=FakeAccount
        with patch.dict(sys.modules,{"live_free_account":fake}):
            self.assertIsNone(verify_authority())
        self.assertEqual(calls[-1],("scope","p04",CAMPAIGN,CASE,1,1,False))


if __name__ == "__main__":
    unittest.main()
