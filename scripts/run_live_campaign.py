"""Offline preparation and reservation dry-run for P04 durable workflow evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "plan_validity_order",
    "step_quality",
    "cancellation",
    "duplicate_delivery",
    "transient_failure",
    "permanent_failure",
    "lease_expiry",
    "crash_recovery",
}
CASE_CAPS = {
    "provider_calls_per_trial": 3,
    "input_tokens_per_trial": 12288,
    "output_tokens_per_trial": 1536,
    "provider_calls_per_step": 1,
    "input_tokens_per_call": 4096,
    "output_tokens_per_call": 512,
    "task_timeout_seconds": 120,
    "provider_call_timeout_seconds": 30,
}


class CampaignError(ValueError):
    """Raised when campaign inputs are incomplete or inconsistent."""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignError(f"invalid JSON: {path.name}") from exc
    if not isinstance(data, dict):
        raise CampaignError(f"expected JSON object: {path.name}")
    return data


def validate_cases(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    if len(rows) != 60 or len({row.get("id") for row in rows}) != 60:
        raise CampaignError("dataset requires 60 unique cases")

    split_counts = {
        split: sum(row.get("split") == split for row in rows)
        for split in ("development", "holdout")
    }
    if split_counts != {"development": 18, "holdout": 42}:
        raise CampaignError("dataset split must be 18/42")

    language_counts = {
        language: sum(row.get("language") == language for row in rows)
        for language in ("en", "pt-BR")
    }
    if language_counts != {"en": 36, "pt-BR": 24}:
        raise CampaignError("language coverage must be 36/24")

    families = {row.get("family") for row in rows}
    if families != FAMILIES or any(
        sum(row.get("family") == family for row in rows) < 3 for family in FAMILIES
    ):
        raise CampaignError("required scenario families are incomplete")

    groups: dict[str, set[str]] = {}
    required_services = {"PostgreSQL", "LocalStack SQS", "Redis Streams"}
    for row in rows:
        groups.setdefault(row.get("source_group"), set()).add(row.get("split"))
        if (
            not isinstance(row.get("request"), str)
            or not row["request"]
            or not isinstance(row.get("expected"), dict)
            or not isinstance(row.get("prohibited_effects"), list)
            or not row["prohibited_effects"]
            or row.get("limits") != CASE_CAPS
            or not required_services.issubset(set(row.get("service_prerequisites", [])))
            or row.get("expected", {}).get("provider_billing_claim") == "exactly_once"
        ):
            raise CampaignError(f"case contract invalid: {row.get('id', 'unknown')}")

    if any(len(splits) > 1 for splits in groups.values()):
        raise CampaignError("related cases cross development/holdout split")
    if len(groups) != len(rows):
        raise CampaignError("scenario source groups must be unique")
    if manifest.get("case_count") != 60 or set(manifest.get("families", [])) != FAMILIES:
        raise CampaignError("manifest mismatch")


def read_cases(path: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CampaignError("dataset unavailable") from exc
    if hashlib.sha256(raw).hexdigest() != manifest.get("sha256_cases_jsonl"):
        raise CampaignError("dataset SHA-256 mismatch")
    try:
        rows = [
            json.loads(line)
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError("dataset must be UTF-8 JSONL") from exc
    validate_cases(rows, manifest)
    return rows


def validate_config(config: dict[str, Any]) -> None:
    if config.get("trials_per_case") != 3 or config.get("pilot_trials_per_case") != 1:
        raise CampaignError("trial configuration invalid")
    if config.get("per_case_caps") != CASE_CAPS:
        raise CampaignError("per-case caps invalid")

    execution = config.get("execution", {})
    retry_and_timeout = {
        "max_retries": 0,
        "provider_max_retries": 0,
        "worker_max_attempts": 3,
        "timeout_seconds_per_call": 30,
        "task_timeout_seconds": 120,
    }
    if any(execution.get(key) != value for key, value in retry_and_timeout.items()):
        raise CampaignError("retry and timeout policy invalid")

    plan = config.get("planned_reservations", {})
    reservation_totals = {
        "pilot_max_calls": 18,
        "primary_campaign_max_calls": 540,
        "confirmation_max_calls": 180,
        "all_stages_max_calls_if_additive": 738,
    }
    if any(plan.get(key) != value for key, value in reservation_totals.items()):
        raise CampaignError("reservation totals invalid")

    if (
        config.get("generation_enabled") is not False
        or config.get("sqlite_demo_counts_as_service_evidence") is not False
        or config.get("exactly_once_provider_billing_claim") is not False
    ):
        raise CampaignError("generation, service, or billing guard invalid")
    if config.get("cumulative_caps", {}).get("authorized_paid_spend_usd") != 0:
        raise CampaignError("paid spend must stay USD 0")


def grade_case(
    case: dict[str, Any], observation: Any, *, provenance: str = "live"
) -> list[str]:
    if provenance not in {"live", "fake", "replay"}:
        return ["invalid provenance"]
    if provenance != "live":
        return ["fixture/replay cannot count as live provider and service evidence"]
    if not isinstance(observation, dict):
        return ["observation schema invalid"]

    expected = case["expected"]
    family = case["family"]
    errors: list[str] = []

    if observation.get("task_status") != expected.get("terminal_status"):
        errors.append("terminal task state mismatch")
    if observation.get("provider_billing_claim") == "exactly_once":
        errors.append("unsupported exactly-once provider billing claim")
    if observation.get("post_auth_expiry_effect", 0) != 0:
        errors.append("unauthorized post-auth-expiry effect")

    if family == "plan_validity_order":
        if (
            observation.get("plan_valid") is not expected.get("plan_valid")
            or observation.get("planned_steps") != expected.get("planned_steps")
        ):
            errors.append("plan validity or step order mismatch")
        if (
            expected.get("plan_valid") is False
            and observation.get("committed_effects", 0) != 0
        ):
            errors.append("effect committed for invalid plan")
    elif family == "step_quality":
        if observation.get("step_quality_valid") is not expected.get(
            "step_quality_valid"
        ):
            errors.append("step quality mismatch")
        if (
            expected.get("step_quality_valid") is False
            and observation.get("committed_effects", 0) != 0
        ):
            errors.append("effect committed for invalid step")
    elif family == "cancellation":
        if (
            observation.get("task_status") != "cancelled"
            or observation.get("post_cancel_effects") != 0
        ):
            errors.append("unauthorized post-cancellation effect")
    elif family == "duplicate_delivery":
        keys = observation.get("committed_effect_keys", [])
        if (
            not isinstance(keys, list)
            or len(keys) != len(set(keys))
            or observation.get("unique_committed_effects")
            != expected.get("unique_committed_effects")
        ):
            errors.append("duplicate committed effect")
    elif family == "transient_failure":
        retries = observation.get("retry_count")
        if (
            not isinstance(retries, int)
            or retries != expected.get("retry_count")
            or retries > 3
        ):
            errors.append("transient retry bound exceeded")
        if (
            expected.get("terminal_status") == "failed"
            and observation.get("dead_lettered") is not True
        ):
            errors.append("exhausted task missing dead letter")
    elif family == "permanent_failure":
        if (
            observation.get("retry_count") != 0
            or observation.get("dead_lettered") is not True
        ):
            errors.append("permanent failure retry/DLQ contract mismatch")
    elif family == "lease_expiry":
        lease_fields = (
            "claim_before_expiry",
            "claim_after_expiry",
            "old_worker_commit_allowed",
        )
        if any(
            observation.get(field) is not expected.get(field)
            for field in lease_fields
        ):
            errors.append("lease ownership/recovery mismatch")
    elif family == "crash_recovery":
        crash_fields = (
            "provider_response_before_crash",
            "effect_committed_before_crash",
        )
        if any(
            observation.get(field) is not expected.get(field)
            for field in crash_fields
        ):
            errors.append("provider response/effect commit boundary mismatch")
        if (
            observation.get("recovery_checkpoint") != "durable"
            or observation.get("duplicate_effects", 0) != 0
        ):
            errors.append("crash recovery/idempotency mismatch")
    return errors


def summarize(
    stage: str,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    if stage == "pilot":
        selected = [row for row in rows if row["split"] == "development"][:6]
    elif stage in {"development", "holdout"}:
        selected = [row for row in rows if row["split"] == stage]
    else:
        raise CampaignError("unknown stage")

    trials_per_case = (
        config["pilot_trials_per_case"] if stage == "pilot" else config["trials_per_case"]
    )
    trials = len(selected) * trials_per_case
    caps = config["per_case_caps"]
    calls = trials * caps["provider_calls_per_trial"]
    plan = config["planned_reservations"]
    blockers = [
        "budget.authorized_paid_spend_usd_zero",
        "approval.expanded_campaign_approval",
        "approval.independent_dataset_and_rubric_review",
        "approval.clean_context_phase_verification",
        "approval.service_identity_and_ports",
        "cumulative_caps.requests",
        "cumulative_caps.input_tokens",
        "cumulative_caps.output_tokens",
        "cumulative_caps.provider_account_quota",
        "cumulative_caps.confirmation_funding",
        "execution.min_seconds_between_calls",
        "execution.max_wall_clock_minutes",
        "execution.persistent_cumulative_ledger",
        "execution.serialized_campaign_lease",
        "provider.authenticated_model_catalog_preflight",
    ]
    strata = {
        "family": {
            family: sum(row["family"] == family for row in selected)
            for family in sorted(FAMILIES)
        },
        "language": {
            language: sum(row["language"] == language for row in selected)
            for language in ("en", "pt-BR")
        },
        "split": {
            split: sum(row["split"] == split for row in selected)
            for split in ("development", "holdout")
        },
    }
    planned_fields = (
        "primary_campaign_max_calls",
        "primary_campaign_max_input_tokens",
        "primary_campaign_max_output_tokens",
        "confirmation_fresh_cases",
        "confirmation_max_calls",
        "confirmation_max_input_tokens",
        "confirmation_max_output_tokens",
        "all_stages_max_calls_if_additive",
        "all_stages_max_input_tokens_if_additive",
        "all_stages_max_output_tokens_if_additive",
    )
    return {
        "status": "DRY_RUN",
        "stage": stage,
        "dataset_sha256": manifest["sha256_cases_jsonl"],
        "cases": len(selected),
        "logical_trials": trials,
        "max_provider_calls": calls,
        "max_input_tokens": trials * caps["input_tokens_per_trial"],
        "max_output_tokens": trials * caps["output_tokens_per_trial"],
        "strata": strata,
        "campaign_plan": {key: plan[key] for key in planned_fields},
        "authorized_paid_spend_usd": 0,
        "blockers": blockers,
        "generation_authorized": False,
        "provider_accessed": False,
        "credentials_read": False,
        "network_accessed": False,
        "docker_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "evals/live-campaign.json"
    )
    parser.add_argument(
        "--stage", choices=("pilot", "development", "holdout"), required=True
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        config_path = args.config if args.config.is_absolute() else ROOT / args.config
        config = read_json(config_path)
        manifest = read_json(ROOT / config["dataset_manifest"])
        rows = read_cases(ROOT / config["cases_path"], manifest)
        validate_config(config)
        report = summarize(args.stage, rows, config, manifest)
    except (CampaignError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "INCOMPLETE", "error": str(exc)}, sort_keys=True))
        return 2

    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    blocked = {
        **report,
        "status": "INCOMPLETE",
        "reason": "campaign execution is disabled during preparation",
    }
    print(json.dumps(blocked, sort_keys=True))
    return 2


if __name__ == "__main__":
    sys.exit(main())
