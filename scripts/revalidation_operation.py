"""Single-use, authorized current-source synthetic P04 revalidation operation."""
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
import argparse
import socket
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from scripts.campaign_ledger import CampaignLedger
from supportops_async.accounted import AccountedWorkflowRunner, STEPS

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
CASE = "fixture-reviewed-operation-040"
CAMPAIGN = "local-reviewed-operation-040-v1"
MANIFEST = f"artifacts/evals/live/{CAMPAIGN}/manifest.json"
INVOCATION = "artifacts/evidence/reentrant-reviewed-operation-041/invocation.json"
LIVE_RESULT = "artifacts/evidence/reentrant-reviewed-operation-041/live-result.json"
CAPS = {"requests":9,"input_tokens":36864,"output_tokens":4608,"estimated_cost_usd":Decimal("0.0041472")}
RESERVATION = {"calls":3,"input_tokens":12288,"output_tokens":1536,"estimated_cost_usd":Decimal("0.0013824")}
ROOT_SOURCES = (
    "scripts/harness/live_free_account.py",
    "scripts/harness/live_provider_transport.py",
    "scripts/harness/migrate_p01_p04_revalidation.py",
    "shared/policies/groq-free-campaign.json",
    ".planning/llm-live-readiness/phases/039-p01-p04-reviewed-revalidation/AUTHORIZATION.json",
    ".planning/llm-live-readiness/phases/047-p04-reentrant-operation/AUTHORIZATION.json",
)
MODEL = "openai/gpt-oss-20b"
HOST_PORTS = {"postgres":35532,"localstack":35566,"api":35580}


class OperationBlocked(RuntimeError):
    pass


def git(project, *args):
    result = subprocess.run(["git", *args], cwd=project, capture_output=True, timeout=15)
    if result.returncode:
        raise OperationBlocked("source_provenance")
    return result.stdout.decode().strip()


def source_paths(project):
    return sorted(p for p in git(project,"ls-files").splitlines()
                  if p.startswith(("supportops_async/","scripts/","tests/","agent/","evals/"))
                  or p in {"pyproject.toml","uv.lock","harness.yaml"})


def fingerprint(project=PROJECT,lab=LAB):
    paths=source_paths(project)
    git(project,"diff","--quiet","HEAD","--",*paths)
    git(lab,"diff","--quiet","HEAD","--",*ROOT_SOURCES)
    values=[("p04/"+p,hashlib.sha256((project/p).read_bytes()).hexdigest()) for p in paths]
    values += [(p,hashlib.sha256((lab/p).read_bytes()).hexdigest()) for p in ROOT_SOURCES]
    return hashlib.sha256(json.dumps(values,separators=(",",":")).encode()).hexdigest()


def require_applied_migration(lab=LAB):
    result=subprocess.run([sys.executable,str(lab/"scripts/harness/migrate_p01_p04_revalidation.py"),"--dry-run"],cwd=lab,capture_output=True,text=True,timeout=45)
    try: report=json.loads(result.stdout)
    except (ValueError,TypeError): raise OperationBlocked("root_migration_unverified") from None
    if result.returncode or report.get("status")!="ALREADY_APPLIED":
        raise OperationBlocked("root_migration_unverified")
    return report


def require_applied_migration_under_campaign_lease(lab=LAB):
    """Recheck migration under the already-held campaign lease without reacquiring it."""
    sys.path.insert(0, str(lab / "scripts/harness"))
    import migrate_p01_p04_revalidation as migration
    from live_free_account import machine_lease

    try:
        policy = json.loads((lab / migration.POLICY).read_text(encoding="utf-8"))
        with machine_lease(lab / ".runtime/llm-live-readiness/account.lock"):
            records = migration.read_audit(lab)
            registry = migration.read_json(lab, lab / ".runtime/llm-live-readiness/ledger-references.json")
            if (migration.digest(policy) != migration.NEW_SHA
                    or registry.get("policy_sha256") != migration.NEW_SHA
                    or [event for event, _ in records] != ["prepared", "applied"]
                    or migration.marker_path(lab).exists()):
                raise OperationBlocked("root_migration_unverified")
            current = migration.snapshot(lab, policy)
            migration.verify_prefixes(records[0][1], current)
    except Exception:
        raise OperationBlocked("root_migration_unverified") from None


def owner_allocation(project=PROJECT):
    try:
        owner=json.loads((project/"evals/live-execution.json").read_text(encoding="utf-8"))
        allocation=owner["allocations"][CAMPAIGN]
    except (OSError,ValueError,KeyError,TypeError):
        raise OperationBlocked("owner_allocation_invalid") from None
    if (owner.get("project")!="p04" or owner.get("execution_enabled") is not True
            or owner.get("synthetic_only") is not True or owner.get("authorized_paid_spend_usd")!="0.00"
            or CAMPAIGN not in owner.get("approved_campaigns",[])
            or allocation!={"stage":"operation","case_ids":[CASE],"trials_per_case":1,"max_trials":1}):
        raise OperationBlocked("owner_allocation_invalid")
    return owner


def file_hashes(project=PROJECT,lab=LAB):
    own=source_paths(project)
    values={"projects/p04/"+p:hashlib.sha256((project/p).read_bytes()).hexdigest() for p in own}
    values.update({p:hashlib.sha256((lab/p).read_bytes()).hexdigest() for p in ROOT_SOURCES})
    return values


def freeze_manifest(project=PROJECT,lab=LAB):
    require_applied_migration(lab); owner_allocation(project); verify_authority()
    target=project/MANIFEST
    if target.exists() or target.is_symlink(): raise OperationBlocked("manifest_already_frozen")
    policy=json.loads((lab/"shared/policies/groq-free-campaign.json").read_text(encoding="utf-8"))
    if policy.get("projects",{}).get("p04",{}).get("requests")!=747:
        raise OperationBlocked("root_policy_mismatch")
    candidate=git(project,"rev-parse","HEAD")
    value={"campaign":CAMPAIGN,"case":CASE,"stage":"operation","candidate":candidate,
           "fingerprint":fingerprint(project,lab),"authorization_id":"p04-reentrant-operation-047-v1",
           "root_policy_sha256":hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest(),
           "max_provider_calls":3,"max_input_tokens":12288,"max_output_tokens":1536,
           "estimated_cost_usd":"0.0013824","aggregate_logical_ceiling":{"requests":9,"input_tokens":36864,"output_tokens":4608,"estimated_cost_usd":"0.0041472"},
           "files_sha256":file_hashes(project,lab),"human_review":"PENDING","promotion":"PENDING"}
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(value,indent=2,sort_keys=True)+"\n");stream.flush();os.fsync(stream.fileno())
    return value


def validate(project=PROJECT,lab=LAB, *, campaign_lease_held=False):
    if campaign_lease_held:
        require_applied_migration_under_campaign_lease(lab)
    else:
        require_applied_migration(lab)
    try:
        manifest=json.loads((project/MANIFEST).read_text())
    except (OSError,ValueError):
        raise OperationBlocked("manifest_missing") from None
    owner_allocation(project)
    policy=json.loads((lab/"shared/policies/groq-free-campaign.json").read_text(encoding="utf-8"))
    if (manifest.get("campaign")!=CAMPAIGN or manifest.get("case")!=CASE
            or manifest.get("stage")!="operation" or manifest.get("authorization_id")!="p04-reentrant-operation-047-v1"
            or manifest.get("fingerprint")!=fingerprint(project,lab) or manifest.get("files_sha256")!=file_hashes(project,lab)
            or manifest.get("root_policy_sha256")!=hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()
            or manifest.get("max_provider_calls")!=3 or manifest.get("max_input_tokens")!=12288
            or manifest.get("max_output_tokens")!=1536 or manifest.get("estimated_cost_usd")!="0.0013824"
            or manifest.get("aggregate_logical_ceiling")!={"requests":9,"input_tokens":36864,"output_tokens":4608,"estimated_cost_usd":"0.0041472"}
            or manifest.get("human_review")!="PENDING" or manifest.get("promotion")!="PENDING"):
        raise OperationBlocked("manifest_mismatch")
    candidate=manifest.get("candidate")
    if not isinstance(candidate,str) or len(candidate)!=40:
        raise OperationBlocked("candidate_missing")
    git(project,"merge-base","--is-ancestor",candidate,"HEAD")
    git(project,"diff","--quiet",candidate,"--",*source_paths(project))
    if (project/INVOCATION).exists() or (project/LIVE_RESULT).exists():
        raise OperationBlocked("invocation_already_started")
    verify_authority()
    return manifest


def verify_authority():
    """Read-only exact original history and explicit authority; no credentials or dispatch."""
    sys.path.insert(0,str(LAB/"scripts/harness"))
    from live_free_account import SharedAccount
    policy=json.loads((LAB/"shared/policies/groq-free-campaign.json").read_text())
    account=SharedAccount(LAB,policy)
    account._reviewed_revalidation(account._history(),"p04",CAMPAIGN,CASE,1,1,False)


class LazySession:
    provenance="live"

    def __init__(self,factory):
        self.factory,self.session=factory,None

    def preview(self,envelope):
        if self.session is None:
            self.session=self.factory()
        envelope["campaign_id"]=CAMPAIGN
        return self.session.preview(envelope)

    def complete(self,envelope):
        envelope["campaign_id"]=CAMPAIGN
        return self.session.complete(envelope)


def reserve(path):
    ledger=CampaignLedger(path,campaign_id=CAMPAIGN)
    if ledger.reserved_trials():
        raise OperationBlocked("prior_operation_no_replay")
    ledger.reserve(case_id=CASE,trial=1,calls=RESERVATION["calls"],
                   input_tokens=RESERVATION["input_tokens"],output_tokens=RESERVATION["output_tokens"],
                   estimated_cost_usd=RESERVATION["estimated_cost_usd"],caps=CAPS)
    return ledger


def write_once(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with path.open("x",encoding="utf-8",newline="\n") as stream:
            stream.write(json.dumps(value,indent=2,sort_keys=True)+"\n")
            stream.flush();os.fsync(stream.fileno())
    except FileExistsError:
        raise OperationBlocked("invocation_already_started") from None


def live_preconditions():
    from scripts.credential_presence import NAMES, preflight

    report = preflight(LAB, os.environ)
    # ProviderSession deliberately reads numbered slots from LAB/.env. Process
    # slots are diagnostic-only until the shared provider contract changes.
    if report["status"] != "PRESENT":
        return {"status":"BLOCKED_PRECONDITION","reason":"root_credentials_missing",
                "required_variables_present":{name:False for name in NAMES},
                "provider_root_env_slots":report["provider_root_env_slots"],
                "process_slots":report["process_slots"],
                "credential_source":"root_env","values_exposed":False,
                "provider_accessed":False,"generation_calls":0}
    return None


def service_preconditions():
    dsn="postgresql://supportops:supportops@127.0.0.1:35532/supportops"
    endpoint="http://127.0.0.1:35566"
    for name,host,port in (("postgres","127.0.0.1",HOST_PORTS["postgres"]),
                           ("localstack","127.0.0.1",HOST_PORTS["localstack"])):
        try:
            with socket.create_connection((host,port),timeout=0.5): pass
        except OSError:
            return {"status":"BLOCKED_PRECONDITION","reason":f"{name}_unreachable","provider_accessed":False}
    return dsn,endpoint


def execute():
    if os.getenv("LLM_MODE","fake")!="live":
        raise OperationBlocked("explicit_live_required")
    validate()
    verify_authority()
    missing=live_preconditions()
    if missing:
        print(json.dumps(missing,sort_keys=True))
        return 2
    services=service_preconditions()
    if isinstance(services,dict):
        print(json.dumps(services,sort_keys=True))
        return 2
    # Fixed loopback-only service endpoints; no host gateway or production URL.
    import boto3
    import httpx
    import uvicorn
    from opentelemetry import trace
    from supportops_async.api.app import create_app
    from supportops_async.store.postgres import PostgresTaskStore
    from supportops_async.queue.memory import SqsBroker
    from supportops_async.worker import Worker
    sys.path.insert(0,str(LAB/"scripts/harness"))
    from live_free_account import machine_lease
    from live_provider_transport import ProviderSession
    policy=json.loads((LAB/"shared/policies/groq-free-campaign.json").read_text())
    if policy["projects"]["p04"]["requests"]!=747:
        raise OperationBlocked("allocation_not_migrated")
    base=PROJECT/"artifacts/evals/live"
    base.mkdir(parents=True,exist_ok=True)
    with machine_lease(LAB/".runtime/llm-live-readiness/campaign.lock"):
        # Read-only model/account preflight occurs after an exclusive single-use marker.
        frozen=validate(campaign_lease_held=True)
        write_once(PROJECT/INVOCATION,{"campaign":CAMPAIGN,"case":CASE,"trial":1,
                    "candidate":frozen["candidate"],"fingerprint":frozen["fingerprint"],
                    "root_policy_sha256":frozen["root_policy_sha256"],"single_invocation":True,
                    "generation_calls_max":3,"paid_authorized_usd":"0.00"})
        from live_free_account import bounded_catalog_preflight
        preflight=bounded_catalog_preflight()
        if preflight.get("status")!="PASS" or preflight.get("model")!=MODEL or preflight.get("generation_calls")!=0:
            result={"status":"INCOMPLETE","reason":"model_access_preflight","generation_calls":0,
                    "invocation_consumed":True,"workflow_reservation_created":False,"provider_content_saved":False}
            write_once(PROJECT/LIVE_RESULT,result)
            print(json.dumps(result,sort_keys=True));return 2
        ledger=reserve(base/"ledger.sqlite")
        dsn,endpoint=services
        store=PostgresTaskStore(dsn)
        sqs=boto3.client("sqs",endpoint_url=endpoint,region_name="us-east-1",aws_access_key_id="test",aws_secret_access_key="test")
        queue=sqs.create_queue(QueueName="p04-reviewed-041")['QueueUrl']
        dlq=sqs.create_queue(QueueName="p04-reviewed-041-dlq")['QueueUrl']
        broker=SqsBroker(sqs,queue,dlq)
        server=uvicorn.Server(uvicorn.Config(create_app(store,broker),host="127.0.0.1",port=35580,log_level="critical",access_log=False))
        thread=threading.Thread(target=server.run,daemon=True)
        thread.start()
        deadline=time.monotonic()+15
        while not server.started:
            if not thread.is_alive() or time.monotonic()>deadline:
                raise OperationBlocked("local_api_startup")
            time.sleep(.1)
        trace_id=uuid.uuid4().hex
        context={"status":"preparing","trace_id":trace_id,"campaign":CAMPAIGN,"case":CASE}
        out=PROJECT/"artifacts/evidence/reentrant-reviewed-operation-041"
        out.mkdir(parents=True,exist_ok=True)
        try:
            runner=AccountedWorkflowRunner(base/"reviewed-operations-041.sqlite",LazySession(lambda:ProviderSession(LAB,"p04",policy)),allow_live=True,scenario="greeting")
            with httpx.Client(base_url="http://127.0.0.1:35580",timeout=10) as client:
                response=client.post("/tasks",headers={"Idempotency-Key":CASE,"traceparent":f"00-{trace_id}-0123456789abcdef-01"},json={"payload":{"operation_id":CASE},"steps":list(STEPS)})
                if response.status_code!=202:
                    raise OperationBlocked("local_api_submission")
                task_id=response.json()["task_id"]
                context["task_id"]=task_id
                (out/"live-context.json").write_text(json.dumps(context,indent=2)+"\n",encoding="utf-8",newline="\n")
                worker=Worker(store,broker,runner=runner)
                if not worker.run_once():
                    raise OperationBlocked("queue_delivery_missing")
                if runner.last_diagnostic:
                    raise OperationBlocked(runner.last_diagnostic)
                state=client.get("/tasks/"+task_id).json()
                if state["status"]!="done":
                    raise OperationBlocked(runner.last_diagnostic or "worker_operation_incomplete")
                # Same idempotency key must never cause another provider dispatch.
                replay=client.post("/tasks",headers={"Idempotency-Key":CASE},json={"payload":{"operation_id":CASE},"steps":list(STEPS)})
                if replay.status_code!=202 or replay.json()["task_id"]!=task_id:
                    raise OperationBlocked("duplicate_task_mismatch")
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect((base/"reviewed-operations-041.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
                rows=db.execute("SELECT receipt,input_tokens,output_tokens FROM attempts WHERE status='ok'").fetchall()
            if len(rows)!=2:
                raise OperationBlocked("receipt_count")
            inp,out=sum(r[1] for r in rows),sum(r[2] for r in rows)
            cost=(Decimal(inp)*Decimal("0.075")+Decimal(out)*Decimal("0.30"))/1000000
            ledger.complete(case_id=CASE,trial=1,input_tokens=inp,output_tokens=out,actual_cost_usd=cost,outcome="ok",error_class=None)
            provider=trace.get_tracer_provider()
            flushed=bool(provider.force_flush(timeout_millis=10000))
            result={"status":"ok","provider_calls":2,"input_tokens":inp,"output_tokens":out,
                    "receipts":[r[0] for r in rows],"trace_id":trace_id,"telemetry_flushed":flushed,
                    "api_worker_status":"done","duplicate_task_reused":True,"actual_billed_usd":None,
                    "paid_authorized_usd":"0.00","provider_content_saved":False}
            write_once(PROJECT/LIVE_RESULT,result)
            return result
        except Exception as error:
            allowed={"synthetic_contract","prior_work_requires_review","already_reserved","fixture_allocation_exhausted",
                     "uncertain_accounted_attempt","invalid_accounted_receipt","step_contract","duplicate_receipt",
                     "accounted_failure","queue_delivery_missing","worker_operation_incomplete","receipt_count"}
            reason=str(error) if isinstance(error,OperationBlocked) and str(error) in allowed else "diagnostic_uncertain"
            (out/"live-stop.json").write_text(json.dumps({**context,"status":"INCOMPLETE","reason":reason,"replay_allowed":False},indent=2)+"\n",encoding="utf-8",newline="\n")
            ledger.complete(case_id=CASE,trial=1,input_tokens=None,output_tokens=None,actual_cost_usd=None,outcome="incomplete",error_class="unknown")
            write_once(PROJECT/LIVE_RESULT,{"status":"INCOMPLETE","reason":reason,"provider_content_saved":False,
                        "invocation_consumed":True,"reserve_retained":True,"replay_allowed":False})
            raise OperationBlocked(reason) from None
        finally:
            server.should_exit=True
            thread.join(timeout=15)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--freeze-manifest",action="store_true")
    group.add_argument("--validate",action="store_true")
    args=parser.parse_args()
    try:
        if args.freeze_manifest:
            value=freeze_manifest();print(json.dumps({"status":"FROZEN","candidate":value["candidate"],"fingerprint":value["fingerprint"],"root_policy_sha256":value["root_policy_sha256"],"caps":RESERVATION},sort_keys=True));raise SystemExit(0)
        if args.validate:
            value=validate();print(json.dumps({"status":"PASS","candidate":value["candidate"],"fingerprint":value["fingerprint"],"root_policy_sha256":value["root_policy_sha256"]},sort_keys=True));raise SystemExit(0)
        code=execute()
        if code==0: print(json.dumps(json.loads((PROJECT/LIVE_RESULT).read_text()),sort_keys=True))
        raise SystemExit(code)
    except OperationBlocked as error:
        allowed={"explicit_live_required","source_provenance","manifest_missing","manifest_mismatch","candidate_missing",
                 "root_migration_unverified","owner_allocation_invalid","root_policy_mismatch","invocation_already_started",
                 "allocation_not_migrated","prior_operation_no_replay","local_api_startup","local_api_submission",
                 "queue_delivery_missing","worker_operation_incomplete","duplicate_task_mismatch","receipt_count",
                 "synthetic_contract","prior_work_requires_review","already_reserved","fixture_allocation_exhausted",
                 "uncertain_accounted_attempt","invalid_accounted_receipt","step_contract","duplicate_receipt","accounted_failure"}
        print(json.dumps({"status":"INCOMPLETE","reason":str(error) if str(error) in allowed else "operation_stopped_no_replay"}))
        if (PROJECT/INVOCATION).exists() and not (PROJECT/LIVE_RESULT).exists():
            try:
                write_once(PROJECT/LIVE_RESULT,{"status":"INCOMPLETE","reason":"operation_stopped_no_replay",
                            "invocation_consumed":True,"provider_content_saved":False,"replay_allowed":False})
            except OperationBlocked:
                pass
        raise SystemExit(2)
    except Exception:
        print(json.dumps({"status":"INCOMPLETE","reason":"operation_stopped_no_replay"}))
        if (PROJECT/INVOCATION).exists() and not (PROJECT/LIVE_RESULT).exists():
            try:
                write_once(PROJECT/LIVE_RESULT,{"status":"INCOMPLETE","reason":"operation_stopped_no_replay",
                            "invocation_consumed":True,"provider_content_saved":False,"replay_allowed":False})
            except OperationBlocked:
                pass
        raise SystemExit(2)
