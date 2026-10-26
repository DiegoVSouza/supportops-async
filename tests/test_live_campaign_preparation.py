from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.run_live_campaign import (
    CampaignError,
    grade_case,
    read_cases,
    read_json,
    summarize,
    validate_cases,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_json(ROOT / "evals/live-campaign.json")
MANIFEST = read_json(ROOT / CONFIG["dataset_manifest"])
CASES = read_cases(ROOT / CONFIG["cases_path"], MANIFEST)


class CampaignPreparationTests(unittest.TestCase):
    def test_dataset_counts_and_family_contracts(self) -> None:
        self.assertEqual(len(CASES), 60)
        self.assertEqual(sum(row["split"] == "development" for row in CASES), 18)
        self.assertEqual(sum(row["split"] == "holdout" for row in CASES), 42)
        self.assertEqual(sum(row["language"] == "en" for row in CASES), 36)
        self.assertEqual(sum(row["language"] == "pt-BR" for row in CASES), 24)
        self.assertTrue(
            all(
                {"PostgreSQL", "LocalStack SQS", "Redis Streams"}.issubset(
                    row["service_prerequisites"]
                )
                for row in CASES
            )
        )

    def test_related_source_cannot_cross_splits(self) -> None:
        rows = [dict(row) for row in CASES]
        rows[0] = dict(rows[0])
        rows[0]["source_group"] = rows[30]["source_group"]
        with self.assertRaisesRegex(CampaignError, "cross"):
            validate_cases(rows, MANIFEST)

    def test_plan_order_and_invalid_plan_effect_are_rejected(self) -> None:
        case = next(
            row
            for row in CASES
            if row["family"] == "plan_validity_order"
            and row["expected"]["plan_valid"] is False
        )
        observation = {
            "task_status": "failed",
            "plan_valid": False,
            "planned_steps": ["refund"],
            "committed_effects": 1,
        }
        errors = grade_case(case, observation)
        self.assertIn("plan validity or step order mismatch", errors)
        self.assertIn("effect committed for invalid plan", errors)

    def test_invalid_step_cannot_commit_effect(self) -> None:
        case = next(
            row
            for row in CASES
            if row["family"] == "step_quality"
            and row["expected"]["step_quality_valid"] is False
        )
        errors = grade_case(
            case,
            {"task_status": "failed", "step_quality_valid": False, "committed_effects": 1},
        )
        self.assertIn("effect committed for invalid step", errors)

    def test_duplicate_effect_and_exact_once_billing_claim_are_rejected(self) -> None:
        case = next(row for row in CASES if row["family"] == "duplicate_delivery")
        observation = {
            "task_status": "done",
            "unique_committed_effects": 1,
            "committed_effect_keys": ["1:triage", "1:triage"],
            "provider_billing_claim": "exactly_once",
        }
        errors = grade_case(case, observation)
        self.assertIn("duplicate committed effect", errors)
        self.assertIn("unsupported exactly-once provider billing claim", errors)

    def test_cancellation_and_expiry_effects_are_rejected(self) -> None:
        case = next(row for row in CASES if row["family"] == "cancellation")
        errors = grade_case(
            case,
            {
                "task_status": "cancelled",
                "post_cancel_effects": 1,
                "post_auth_expiry_effect": 1,
            },
        )
        self.assertIn("unauthorized post-cancellation effect", errors)
        self.assertIn("unauthorized post-auth-expiry effect", errors)

        lease = next(row for row in CASES if row["family"] == "lease_expiry")
        errors = grade_case(
            lease,
            {
                "task_status": "done",
                "claim_before_expiry": True,
                "claim_after_expiry": False,
                "old_worker_commit_allowed": True,
            },
        )
        self.assertIn("lease ownership/recovery mismatch", errors)

    def test_transient_and_permanent_failure_contracts(self) -> None:
        transient = next(
            row
            for row in CASES
            if row["family"] == "transient_failure"
            and row["expected"]["terminal_status"] == "failed"
        )
        errors = grade_case(
            transient,
            {"task_status": "failed", "retry_count": 3, "dead_lettered": True},
        )
        self.assertIn("transient retry bound exceeded", errors)

        permanent = next(row for row in CASES if row["family"] == "permanent_failure")
        errors = grade_case(
            permanent,
            {"task_status": "failed", "retry_count": 1, "dead_lettered": False},
        )
        self.assertIn("permanent failure retry/DLQ contract mismatch", errors)

    def test_crash_boundary_distinguishes_response_and_effect_commit(self) -> None:
        case = next(
            row
            for row in CASES
            if row["family"] == "crash_recovery"
            and row["expected"]["effect_committed_before_crash"]
        )
        observation = {
            "task_status": "done",
            "provider_response_before_crash": True,
            "effect_committed_before_crash": False,
            "recovery_checkpoint": "none",
            "duplicate_effects": 1,
        }
        errors = grade_case(case, observation)
        self.assertIn("provider response/effect commit boundary mismatch", errors)
        self.assertIn("crash recovery/idempotency mismatch", errors)

    def test_offline_dry_run_and_fail_closed_generation(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-S",
                str(ROOT / "scripts/run_live_campaign.py"),
                "--stage",
                "pilot",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(
            (report["cases"], report["logical_trials"], report["max_provider_calls"]),
            (6, 6, 18),
        )
        self.assertEqual(report["campaign_plan"]["primary_campaign_max_calls"], 540)
        self.assertEqual(report["campaign_plan"]["confirmation_max_calls"], 180)
        self.assertEqual(report["campaign_plan"]["all_stages_max_calls_if_additive"], 738)
        for field in ("provider_accessed", "credentials_read", "network_accessed", "docker_mutated"):
            self.assertFalse(report[field])
        self.assertIn("budget.authorized_paid_spend_usd_zero", report["blockers"])

        development = summarize("development", CASES, CONFIG, MANIFEST)
        holdout = summarize("holdout", CASES, CONFIG, MANIFEST)
        self.assertEqual(
            (development["cases"], development["logical_trials"], development["max_provider_calls"]),
            (18, 54, 162),
        )
        self.assertEqual(
            (holdout["cases"], holdout["logical_trials"], holdout["max_provider_calls"]),
            (42, 126, 378),
        )

        blocked = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run_live_campaign.py"), "--stage", "pilot"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(json.loads(blocked.stdout)["status"], "INCOMPLETE")

    def test_fixture_does_not_count_as_real_service_or_provider(self) -> None:
        self.assertEqual(
            grade_case(CASES[0], {}, provenance="fake"),
            ["fixture/replay cannot count as live provider and service evidence"],
        )

    def test_resume_inspection_is_read_only_and_rejects_unknown_campaign(self) -> None:
        from scripts import run_live_campaign
        from scripts.campaign_ledger import CampaignLedger

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger_path = root / "artifacts/evals/live/ledger.sqlite"
            ledger = CampaignLedger(ledger_path, campaign_id="campaign-a")
            empty_output = StringIO()
            with patch.object(run_live_campaign, "ROOT", root), redirect_stdout(
                empty_output
            ):
                self.assertEqual(
                    run_live_campaign.main(["--resume", "unknown", "--dry-run"]),
                    2,
                )
            self.assertIn("campaign has no recorded attempts", empty_output.getvalue())
            ledger.reserve(
                case_id="case-1",
                trial=1,
                input_tokens=20,
                output_tokens=10,
                estimated_cost_usd=Decimal("0.02"),
                caps={
                    "requests": 1,
                    "input_tokens": 100,
                    "output_tokens": 100,
                    "estimated_cost_usd": Decimal("0.10"),
                },
            )
            output = StringIO()
            with patch.object(run_live_campaign, "ROOT", root), redirect_stdout(output):
                self.assertEqual(
                    run_live_campaign.main(
                        ["--resume", "campaign-a", "--dry-run"]
                    ),
                    0,
                )
            report = json.loads(output.getvalue())
            self.assertEqual(report["project"], "p04")
            self.assertEqual(report["attempts"][0]["event"], "reserved")
            self.assertEqual(report["cumulative_usage"]["requests"], "1")
            self.assertFalse(report["provider_accessed"])


if __name__ == "__main__":
    unittest.main()
