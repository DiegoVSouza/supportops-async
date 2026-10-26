"""Generate one synthetic task plan with Groq and execute it locally."""
from __future__ import annotations
import json, os, random, time
from datetime import UTC, datetime
from pathlib import Path
from groq import Groq
from supportops_async.live_groq import validate_plan
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.queue.contracts import BrokerMessage
from supportops_async.worker import Worker
from supportops_async.worker.runner import FakeRunner

PROJECT=Path(__file__).resolve().parents[1]; LAB=Path(__file__).resolve().parents[3]; MODEL="openai/gpt-oss-20b"

def keys():
    for line in (LAB/".env").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            name,value=line.split("=",1); name=name.strip()
            if name.startswith("GROQ_API_KEY") and value.strip() and name not in os.environ: os.environ[name]=value.strip().strip("\"'")
    return list(dict.fromkeys(os.getenv(n,"").strip() for n in [f"GROQ_API_KEY_{i}" for i in range(1,5)] if os.getenv(n,"")))

def main():
    result={"provider":"groq","model":MODEL,"status":"INCOMPLETE","exit_code":1,"started_at_utc":datetime.now(UTC).isoformat(),"cost_usd":"PENDING"}; code=1
    try:
        if os.getenv("LLM_MODE","").lower()!="live": raise RuntimeError("explicit LLM_MODE=live required")
        credentials=keys(); result["credential_count"]=len(credentials)
        available=[]
        for key in credentials:
            client=Groq(api_key=key,max_retries=0,timeout=20)
            if any(item.id==MODEL for item in client.models.list().data): available.append(key)
        result["model_available_key_count"]=len(available)
        if not available: raise RuntimeError("requested model unavailable in authenticated catalog")
        prompt='For the synthetic support request "How do I find the tracking link for a delayed parcel?", return JSON only as {"steps":["triage","draft_reply"]}. Use only the listed step names, in that order; no external action or refund.'
        response=None
        for attempt,key in enumerate(available[:4]):
            try:
                response=Groq(api_key=key,max_retries=0,timeout=20).chat.completions.create(model=MODEL,messages=[{"role":"user","content":prompt}],max_completion_tokens=128,temperature=1,reasoning_effort="low")
                break
            except Exception as exc:
                status=getattr(exc,"status_code",None)
                if status not in {408,409,429,500,502,503,504} and type(exc).__name__ not in {"Timeout","APIConnectionError"}: raise RuntimeError(f"provider rejection: {type(exc).__name__}, status={status}") from None
                if attempt>=min(3,len(available)-1): raise RuntimeError("transient retry limit reached") from None
                headers=getattr(getattr(exc,"response",None),"headers",{})
                try: delay=float(headers.get("retry-after")) if status==429 and headers.get("retry-after") else min(.25*2**attempt+random.random()*.1,2)
                except (TypeError,ValueError): delay=min(.25*2**attempt+random.random()*.1,2)
                if not 0<=delay<=2: raise RuntimeError("retry-after exceeds 2 second cap") from None
                time.sleep(delay)
        plan=validate_plan(response.choices[0].message.content or "")
        store=SQLiteTaskStore(":memory:"); broker=InMemoryBroker()
        task,_=store.create({"steps":plan,"operation_id":"synthetic-p04-plan"},"phase-013-live-plan")
        broker.publish(BrokerMessage(task.task_id)); worker=Worker(store,broker,runner=FakeRunner())
        ran=worker.run_once(); completed=store.get(task.task_id); effects=[store.effect(task.task_id,f"{i}:{step}") for i,step in enumerate(plan,1)]
        checks={"allowlisted_plan":True,"worker_ran":ran,"completed":completed.status.value=="done","one_effect_per_step":len(effects)==len(plan) and all(effects),"steps":[x for x in plan]==["triage","draft_reply"]}
        code=0 if all(value is True or isinstance(value,list) for value in checks.values()) and checks["steps"] else 1
        usage=response.usage
        result.update(status="PASS" if code==0 else "FAIL",assertions=checks,step_count=len(plan),input_tokens=usage.prompt_tokens,output_tokens=usage.completion_tokens,actual_model=response.model)
        store.close()
    except Exception as exc: result["error"]={"class":type(exc).__name__}; code=1
    result.update(exit_code=code,finished_at_utc=datetime.now(UTC).isoformat()); out=PROJECT/"artifacts"/"evidence"; out.mkdir(parents=True,exist_ok=True); stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (out/f"phase-013-groq-{stamp}.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/f"phase-013-groq-{stamp}.txt").write_text(f"Command: LLM_MODE=live uv run --extra live --group dev python scripts/run_live_groq_eval.py\nExit code: {code}\nSanitized result: {json.dumps(result,sort_keys=True)}\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True)); return code

if __name__=="__main__": raise SystemExit(main())
