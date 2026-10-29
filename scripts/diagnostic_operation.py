"""Fixed local synthetic HTTP/SQS/Worker operation with accounted generation."""
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from decimal import Decimal
from pathlib import Path

from scripts.campaign_ledger import CampaignLedger
from supportops_async.accounted import AccountedWorkflowRunner, STEPS

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
CASE = "fixture-diagnostic-01"
MANIFEST = "artifacts/evals/live/local-diagnostic-v1/manifest.json"


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
    shared=["scripts/harness/live_free_account.py","scripts/harness/live_provider_transport.py","shared/policies/groq-free-campaign.json"]
    git(lab,"diff","--quiet","HEAD","--",*shared)
    values=[("p04/"+p,hashlib.sha256((project/p).read_bytes()).hexdigest()) for p in paths]
    values += [(p,hashlib.sha256((lab/p).read_bytes()).hexdigest()) for p in shared]
    return hashlib.sha256(json.dumps(values,separators=(",",":")).encode()).hexdigest()


def validate(project=PROJECT,lab=LAB):
    try:
        manifest=json.loads((project/MANIFEST).read_text())
        owner=json.loads((project/"evals/live-execution.json").read_text())
    except (OSError,ValueError):
        raise OperationBlocked("manifest_missing") from None
    if (manifest.get("campaign")!="local-diagnostic-v1" or manifest.get("case")!=CASE
            or manifest.get("fingerprint")!=fingerprint(project,lab) or owner.get("execution_enabled") is not True):
        raise OperationBlocked("manifest_mismatch")
    candidate=manifest.get("candidate")
    if not isinstance(candidate,str) or len(candidate)!=40:
        raise OperationBlocked("candidate_missing")
    git(project,"merge-base","--is-ancestor",candidate,"HEAD")
    git(project,"diff","--quiet",candidate,"--",*source_paths(project))


def verify_authority():
    """Read-only exact original history and explicit authority; no credentials or dispatch."""
    sys.path.insert(0,str(LAB/"scripts/harness"))
    from live_free_account import SharedAccount
    policy=json.loads((LAB/"shared/policies/groq-free-campaign.json").read_text())
    account=SharedAccount(LAB,policy)
    account._reviewed_p04_diagnostic(account._history(),CASE,1)


class LazySession:
    provenance="live"

    def __init__(self,factory):
        self.factory,self.session=factory,None

    def preview(self,envelope):
        if self.session is None:
            self.session=self.factory()
        envelope["campaign_id"]="local-diagnostic-v1"
        return self.session.preview(envelope)

    def complete(self,envelope):
        envelope["campaign_id"]="local-diagnostic-v1"
        return self.session.complete(envelope)


def reserve(path):
    ledger=CampaignLedger(path,campaign_id="local-diagnostic-v1")
    if ledger.reserved_trials():
        raise OperationBlocked("prior_operation_no_replay")
    ledger.reserve(case_id=CASE,trial=1,calls=3,input_tokens=12288,output_tokens=1536,
                   estimated_cost_usd=Decimal("0.0013824"),caps={"requests":6,"input_tokens":24576,"output_tokens":3072,
                   "estimated_cost_usd":Decimal("0.0027648")})
    return ledger


def execute():
    if os.getenv("LLM_MODE","fake")!="live":
        raise OperationBlocked("explicit_live_required")
    validate()
    verify_authority()
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
    if policy["projects"]["p04"]["requests"]!=744:
        raise OperationBlocked("allocation_not_migrated")
    base=PROJECT/"artifacts/evals/live"
    base.mkdir(parents=True,exist_ok=True)
    with machine_lease(LAB/".runtime/llm-live-readiness/campaign.lock"):
        validate()
        verify_authority()
        ledger=reserve(base/"ledger.sqlite")
        store=PostgresTaskStore("postgresql://supportops:supportops@127.0.0.1:35432/supportops")
        sqs=boto3.client("sqs",endpoint_url="http://127.0.0.1:34566",region_name="us-east-1",aws_access_key_id="test",aws_secret_access_key="test")
        queue=sqs.create_queue(QueueName="p04-diagnostic-031")['QueueUrl']
        dlq=sqs.create_queue(QueueName="p04-diagnostic-031-dlq")['QueueUrl']
        broker=SqsBroker(sqs,queue,dlq)
        server=uvicorn.Server(uvicorn.Config(create_app(store,broker),host="127.0.0.1",port=35480,log_level="critical",access_log=False))
        thread=threading.Thread(target=server.run,daemon=True)
        thread.start()
        deadline=time.monotonic()+15
        while not server.started:
            if not thread.is_alive() or time.monotonic()>deadline:
                raise OperationBlocked("local_api_startup")
            time.sleep(.1)
        trace_id=uuid.uuid4().hex
        context={"status":"preparing","trace_id":trace_id,"campaign":"local-diagnostic-v1","case":CASE}
        out=PROJECT/"artifacts/evidence/reviewed-diagnostic-031"
        out.mkdir(parents=True,exist_ok=True)
        try:
            runner=AccountedWorkflowRunner(base/"diagnostic-operations.sqlite",LazySession(lambda:ProviderSession(LAB,"p04",policy)),allow_live=True,scenario="greeting")
            with httpx.Client(base_url="http://127.0.0.1:35480",timeout=10) as client:
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
            with closing(sqlite3.connect((base/"diagnostic-operations.sqlite").resolve().as_uri()+"?mode=ro",uri=True)) as db:
                rows=db.execute("SELECT receipt,input_tokens,output_tokens FROM attempts WHERE status='ok'").fetchall()
            if len(rows)!=2:
                raise OperationBlocked("receipt_count")
            inp,out=sum(r[1] for r in rows),sum(r[2] for r in rows)
            cost=(Decimal(inp)*Decimal("0.075")+Decimal(out)*Decimal("0.30"))/1000000
            ledger.complete(case_id=CASE,trial=1,input_tokens=inp,output_tokens=out,actual_cost_usd=cost,outcome="ok",error_class=None)
            provider=trace.get_tracer_provider()
            flushed=bool(provider.force_flush(timeout_millis=10000))
            return {"status":"ok","provider_calls":2,"input_tokens":inp,"output_tokens":out,
                    "receipts":[r[0] for r in rows],"trace_id":trace_id,"telemetry_flushed":flushed,
                    "api_worker_status":"done","duplicate_task_reused":True,"actual_billed_usd":None}
        except Exception as error:
            allowed={"synthetic_contract","prior_work_requires_review","already_reserved","fixture_allocation_exhausted",
                     "uncertain_accounted_attempt","invalid_accounted_receipt","step_contract","duplicate_receipt",
                     "accounted_failure","queue_delivery_missing","worker_operation_incomplete","receipt_count"}
            reason=str(error) if isinstance(error,OperationBlocked) and str(error) in allowed else "diagnostic_uncertain"
            (out/"live-stop.json").write_text(json.dumps({**context,"status":"INCOMPLETE","reason":reason,"replay_allowed":False},indent=2)+"\n",encoding="utf-8",newline="\n")
            ledger.complete(case_id=CASE,trial=1,input_tokens=None,output_tokens=None,actual_cost_usd=None,outcome="incomplete",error_class="unknown")
            raise OperationBlocked(reason) from None
        finally:
            server.should_exit=True
            thread.join(timeout=15)


if __name__=="__main__":
    try:
        result=execute()
        print(json.dumps(result))
        raise SystemExit(0 if result["telemetry_flushed"] else 2)
    except OperationBlocked as error:
        allowed={"explicit_live_required","source_provenance","manifest_missing","manifest_mismatch",
                 "candidate_missing","allocation_not_migrated","prior_operation_no_replay","local_api_startup",
                 "local_api_submission","queue_delivery_missing","worker_operation_incomplete","duplicate_task_mismatch",
                 "receipt_count","synthetic_contract","prior_work_requires_review","already_reserved",
                 "fixture_allocation_exhausted","uncertain_accounted_attempt","invalid_accounted_receipt",
                 "step_contract","duplicate_receipt","accounted_failure"}
        print(json.dumps({"status":"INCOMPLETE","reason":str(error) if str(error) in allowed else "operation_stopped_no_replay"}))
        raise SystemExit(2)
    except Exception:
        print(json.dumps({"status":"INCOMPLETE","reason":"operation_stopped_no_replay"}))
        raise SystemExit(2)
