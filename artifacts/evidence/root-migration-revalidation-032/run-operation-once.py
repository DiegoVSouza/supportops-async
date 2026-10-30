"""Run the one authorized P04 operation after credentials, manifest and local services pass."""
import hashlib,json,os,socket,sqlite3,subprocess,sys,time
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import urlopen

PROJECT=Path(__file__).resolve().parents[3]
LAB=PROJECT.parents[1]
OUT=Path(__file__).resolve().parent
NAMESPACE="p04-root-revalidation-032-live"
IMAGE_TAG=None
PORTS=(35532,35566,35579,35586,35518,35580)
PROTECTED=("artifacts/evidence/check-full.txt",)

def run(command,cwd,env=None,timeout=60):
    if env is None:
        env={k:v for k,v in os.environ.items() if not k.startswith("GROQ_API_KEY")}
    try:
        result=subprocess.run(command,cwd=cwd,env=env,capture_output=True,timeout=timeout)
        code=result.returncode
        stdout=(result.stdout or b"").decode("utf-8",errors="replace")
        stderr=(result.stderr or b"").decode("utf-8",errors="replace")
    except subprocess.TimeoutExpired as error:
        code=124;stdout=error.stdout or b"";stderr=error.stderr or b""
        if isinstance(stdout,bytes): stdout=stdout.decode("utf-8",errors="replace")
        if isinstance(stderr,bytes): stderr=stderr.decode("utf-8",errors="replace")
        stdout+="\ncommand timeout; child was terminated"
    return {"command":command,"cwd":str(cwd),"exit_code":code,"output":stdout+stderr}

def inventory():
    commands={"containers":["docker","ps","-a","--no-trunc","--format","{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}|{{.Label \"com.docker.compose.project\"}}"],
      "networks":["docker","network","ls","--no-trunc","--format","{{.ID}}|{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
      "volumes":["docker","volume","ls","--format","{{.Name}}|{{.Label \"com.docker.compose.project\"}}"],
      "images":["docker","image","ls","--no-trunc","--format","{{.ID}}|{{.Repository}}:{{.Tag}}"]}
    value={}
    for key,command in commands.items():
        r=run(command,PROJECT)
        if r["exit_code"]: raise RuntimeError("docker_inventory_unavailable")
        value[key]=sorted(r["output"].splitlines())
    return value

def keys_present():
    names=["GROQ_API_KEY"]+[f"GROQ_API_KEY_{i}" for i in range(1,5)]
    return {name:bool(os.getenv(name)) for name in names}

def ports_free():
    for port in PORTS:
        with socket.socket() as probe: probe.bind(("127.0.0.1",port))

def verify_live(result):
    if result.get("status")!="ok" or result.get("provider_calls")!=2 or not result.get("telemetry_flushed"):
        raise RuntimeError("operation_not_successful")
    case="fixture-revalidation-01";campaign="local-revalidation-v1"
    db=PROJECT/"artifacts/evals/live/revalidation-operations.sqlite"
    with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as conn:
        steps=conn.execute("SELECT step,status,receipt,input_tokens,output_tokens FROM attempts WHERE operation=? ORDER BY step",(case,)).fetchall()
    receipts={row[2] for row in steps}
    if len(steps)!=2 or any(row[1]!="ok" for row in steps) or receipts!=set(result.get("receipts",[])):
        raise RuntimeError("step_receipt_mismatch")
    provider=PROJECT/"artifacts/evals/live/provider-usage.sqlite"
    with sqlite3.connect(provider.resolve().as_uri()+"?mode=ro",uri=True) as conn:
        uses=conn.execute("SELECT attempt_id,actual_input,actual_output,status,event FROM usage_events WHERE campaign=? AND case_id=? ORDER BY call_index,event",(campaign,case)).fetchall()
    complete=[row for row in uses if row[4]=="completed"]
    if len(complete)!=2 or {row[0] for row in complete}!=receipts or any(row[3]!="ok" for row in complete):
        raise RuntimeError("provider_receipt_mismatch")
    if sum(row[1] for row in complete)!=result["input_tokens"] or sum(row[2] for row in complete)!=result["output_tokens"]:
        raise RuntimeError("provider_usage_mismatch")
    ledger=PROJECT/"artifacts/evals/live/ledger.sqlite"
    with sqlite3.connect(ledger.resolve().as_uri()+"?mode=ro",uri=True) as conn:
        events=conn.execute("SELECT event,reserved_calls,reserved_input_tokens,reserved_output_tokens,outcome,error_class FROM events WHERE campaign_id=? AND case_id=? AND trial=1 ORDER BY sequence",(campaign,case)).fetchall()
    if len(events)!=2 or events[0][:4]!=("reserved",3,12288,1536) or events[1][0]!="completed" or events[1][4]!="ok":
        raise RuntimeError("logical_reservation_mismatch")
    trace=result["trace_id"];data=None
    for delay in (0,1,2,4,8):
        if delay: time.sleep(delay)
        try:
            with urlopen(f"http://127.0.0.1:35586/api/traces/{trace}",timeout=5) as response: data=json.load(response)
        except HTTPError as error:
            if error.code!=404: raise
            data={"data":[]}
        if data.get("data"): break
    spans=data["data"][0]["spans"] if data and data.get("data") else []
    names={span.get("operationName") for span in spans}
    llm=[span for span in spans if span.get("operationName")=="supportops.llm.accounted"]
    if not {"supportops.api.request","supportops.worker.process","supportops.llm.accounted"}<=names or len(llm)!=2:
        raise RuntimeError("trace_correlation_incomplete")
    forbidden=(case,*receipts)
    for span in spans:
        if span.get("logs"): raise RuntimeError("trace_privacy_violation")
        for tag in span.get("tags",[]):
            if "content" in str(tag.get("key","")) or "description" in str(tag.get("key","")):
                raise RuntimeError("trace_privacy_violation")
            if any(value in str(tag.get("value","")) for value in forbidden):
                raise RuntimeError("trace_privacy_violation")
    return {"status":"PASS","provider_calls":2,"input_tokens":result["input_tokens"],"output_tokens":result["output_tokens"],
      "logical_receipt_match":True,"provider_receipt_match":True,"correlated_api_worker_llm_spans":True,
      "trace_privacy_pass":True,"provider_content_saved":False,"actual_billed_usd":None}

def main():
    key_state=keys_present()
    if not all(key_state.values()):
        report={"status":"BLOCKED_PRECONDITION","reason":"credentials_missing","required_variables_present":key_state,
                "values_exposed":False,"provider_accessed":False,"invocation_marker_exists":False}
        (OUT/"live-precondition.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
        print(json.dumps(report,sort_keys=True));return 2
    offline_env={k:v for k,v in os.environ.items() if not k.startswith("GROQ_API_KEY")}
    offline_env["LLM_MODE"]="fake"
    validation=run([sys.executable,"-m","scripts.revalidation_operation","--validate"],PROJECT,offline_env,timeout=90)
    if validation["exit_code"]:
        (OUT/"live-validation.json").write_text(json.dumps(validation,indent=2)+"\n",encoding="utf-8",newline="\n")
        print(json.dumps({"status":"BLOCKED_PRECONDITION","reason":"candidate_validation_failed","provider_accessed":False}));return 2
    before=inventory()
    if any(NAMESPACE in row for kind in ("containers","networks","volumes") for row in before[kind]): raise RuntimeError("live_namespace_already_exists")
    ports_free()
    for image in ("postgres:17.11-alpine3.24","localstack/localstack:4.14.0","redis@sha256:becdda6c7f4b3fb42e42fd7f120bbf5c54c4caaaf16f26da24e4563d2c1f0576","jaegertracing/jaeger:2.18.0"):
        if run(["docker","image","inspect",image,"--format","{{.Id}}"],PROJECT)["exit_code"]: raise RuntimeError("live_image_not_cached")
    baseline={p:hashlib.sha256((PROJECT/p).read_bytes()).hexdigest() for p in PROTECTED}
    compose=["docker","compose","-p",NAMESPACE,"-f",str(OUT/"compose-live.yml")]
    config=run(compose+["config","--quiet"],PROJECT)
    if config["exit_code"]: raise RuntimeError("live_compose_invalid")
    records={"validation":validation,"compose_config":config}
    result={"status":"BLOCKED_PRECONDITION","reason":"services_not_started"}
    verified=None;marker=False;down={"exit_code":0,"output":"no owned resources"};after={};cleanup_reason=None
    invocation_run=None
    up=run(compose+["up","-d","--pull","never","--wait","--wait-timeout","150"],PROJECT,timeout=200)
    records["compose_up"]=up
    try:
        if up["exit_code"]:
            result={"status":"INCOMPLETE","reason":"live_services_not_ready"}
        else:
            env=os.environ.copy()
            env.update({"LLM_MODE":"live","OTEL_SERVICE_NAME":"p04-accounted-local",
                        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT":"http://127.0.0.1:35518/v1/traces"})
            invocation_run=run([sys.executable,"-m","scripts.revalidation_operation"],PROJECT,env,timeout=180)
            marker=(PROJECT/"artifacts/evidence/root-migration-revalidation-032/invocation.json").exists()
            raw_lines=[line for line in invocation_run["output"].splitlines() if line.startswith("{")]
            result=json.loads(raw_lines[-1]) if raw_lines else {"status":"INCOMPLETE","reason":"operation_output_unavailable"}
            records["single_invocation"]={"command":invocation_run["command"],"cwd":invocation_run["cwd"],
                "exit_code":invocation_run["exit_code"],"status":result.get("status"),"reason":result.get("reason"),
                "provider_calls":result.get("provider_calls",result.get("generation_calls")),
                "input_tokens":result.get("input_tokens"),"output_tokens":result.get("output_tokens"),
                "invocation_marker_exists":marker,"provider_content_saved":False,"raw_provider_output_saved":False}
            if invocation_run["exit_code"]==0 and result.get("status")=="ok":
                verified=verify_live(result)
                (OUT/"live-reconciliation.json").write_text(json.dumps(verified,indent=2)+"\n",encoding="utf-8",newline="\n")
    except Exception as error:
        result={"status":"INCOMPLETE","reason":type(error).__name__,"replay_allowed":False}
    finally:
        after_outputs={path:hashlib.sha256((PROJECT/path).read_bytes()).hexdigest() for path in PROTECTED}
        protected=baseline==after_outputs
        (OUT/"live-protected-outputs.json").write_text(json.dumps({"before":baseline,"after":after_outputs,"unchanged":protected},indent=2)+"\n",encoding="utf-8",newline="\n")
        try:
            current=inventory()
            owned=[row for kind in ("containers","networks","volumes") for row in current[kind] if NAMESPACE in row]
            if owned and all(row.endswith("|"+NAMESPACE) for row in owned):
                down=run(compose+["down","--volumes","--remove-orphans"],PROJECT,timeout=120)
            elif owned:
                cleanup_reason="target_namespace_ownership_not_proven"
            after=inventory()
        except Exception:
            cleanup_reason="post_run_inventory_failed"
    clean=False
    if after:
        clean=not any(NAMESPACE in row for kind in ("containers","networks","volumes") for row in after[kind])
        preserved={kind:set(before[kind])<=set(after[kind]) for kind in before}
    else:
        clean=False;preserved={kind:False for kind in before}
    result_summary={"status":"PASS" if result.get("status")=="ok" and verified and down.get("exit_code")==0 and clean and all(preserved.values()) and protected else "INCOMPLETE",
      "operation_status":result.get("status"),"reason":result.get("reason") or cleanup_reason,
      "operation_exit_code":invocation_run["exit_code"] if invocation_run else None,"live_invocation_marker":marker,
      "provider_accessed":bool(marker),"provider_calls":result.get("provider_calls"),"paid_authorized_usd":"0.00",
      "provider_content_saved":False,"historical_reserves_preserved":True,"phase_namespace_empty":clean,
      "docker_baseline_preserved":preserved,"protected_outputs_unchanged":protected,"trace_reconciliation":verified}
    records["cleanup"]=down
    records["final_inventory"]={"namespace_empty":clean,"prior_resources_preserved":preserved}
    (OUT/"live-commands.json").write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8",newline="\n")
    (OUT/"live-result-summary.json").write_text(json.dumps(result_summary,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(result_summary,sort_keys=True))
    return 0 if result_summary["status"]=="PASS" else 2

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status":"INCOMPLETE","reason":type(error).__name__,"provider_content_saved":False,"replay_allowed":False}))
        raise SystemExit(2)
