"""Exclusive local fake gate then one conditional live operation; owned cleanup."""
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
namespace="p04-accounted-030"
records=[]


def run(command,*,env=None,timeout=60):
    result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=timeout)
    records.append({"command":command,"cwd":str(root),"exit_code":result.returncode,"output":result.stdout+result.stderr})
    (out/"commands.json").write_text(json.dumps(records,indent=2)+"\n",newline="\n")
    return result


def inventory():
    result={}
    for kind,command in {"containers":["docker","ps","-a","--no-trunc","--format","{{.ID}}|{{.Names}}|{{.Image}}"],
                         "networks":["docker","network","ls","--no-trunc","--format","{{.ID}}|{{.Name}}"],
                         "volumes":["docker","volume","ls","--format","{{.Name}}"],
                         "images":["docker","image","ls","--no-trunc","--format","{{.ID}}|{{.Repository}}:{{.Tag}}"]}.items():
        response=run(command)
        assert response.returncode==0
        result[kind]=sorted(response.stdout.splitlines())
    return result


assert run(["docker","info","--format","{{.ServerVersion}}"]).returncode==0
before=inventory()
(out/"inventory-before.json").write_text(json.dumps(before,indent=2)+"\n",newline="\n")
existing=run(["docker","ps","-a","-q","--filter","label=com.docker.compose.project="+namespace])
assert existing.returncode==0 and not existing.stdout.strip()
assert not any(namespace in x for x in before["networks"]+before["volumes"])
for port in (35432,34566,36379,35486,35418,35480):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1",port))
for image in ("postgres:17.11-alpine3.24","localstack/localstack:4.14.0","redis@sha256:becdda6c7f4b3fb42e42fd7f120bbf5c54c4caaaf16f26da24e4563d2c1f0576","hashicorp/terraform:1.16.6","jaegertracing/jaeger:2.18.0","python:3.13.12-slim","ghcr.io/astral-sh/uv:0.12.7"):
    assert run(["docker","image","inspect",image,"--format","{{.Id}}"]).returncode==0
compose=["docker","compose","-p",namespace,"-f",str(out/"compose.yml")]
assert run(compose+["config","--quiet"]).returncode==0
work=out/"terraform-work"
assert not work.exists()
work.mkdir()
for source in (root/"infra/terraform").iterdir():
    if source.suffix==".tf" or source.name==".terraform.lock.hcl":
        shutil.copyfile(source,work/source.name)
(out/"terraform.rc").write_text('provider_installation {\n filesystem_mirror {\n path = "/mirror"\n include = ["registry.terraform.io/hashicorp/aws"]\n }\n}\n',newline="\n")
env=dict(os.environ,LLM_MODE="fake",PYTHONPATH=str(root),
         P04_POSTGRES_DSN="postgresql://supportops:supportops@127.0.0.1:35432/supportops",
         P04_LOCALSTACK_ENDPOINT="http://127.0.0.1:34566",P04_TEST_REDIS_URL="redis://127.0.0.1:36379/0",
         P04_PYTEST_BASETEMP="artifacts/evidence/accounted-local-service-030/tmp-full1",
         P04_CHECK_IMAGE_TAG="supportops-async:accounted030",
         P04_TERRAFORM_WORKSPACE=str(work.relative_to(root)),P04_TERRAFORM_MIRROR=str(root/"infra/terraform/.terraform/providers"),
         P04_TERRAFORM_CLI_CONFIG=str(out/"terraform.rc"),P04_TERRAFORM_NETWORK=namespace+"-local",P04_TERRAFORM_ENDPOINT="http://localstack:4566")
code=2
try:
    assert run(compose+["up","-d","--pull","never","--wait","--wait-timeout","150"],timeout=180).returncode==0
    full=run(["uv","run","--locked","--offline","--group","dev","python","scripts/check_full.py"],env=env,timeout=600)
    code=full.returncode
    if code==0:
        live_env=dict(env,LLM_MODE="live",OTEL_SERVICE_NAME="p04-accounted-local",OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://127.0.0.1:35418/v1/traces")
        live=run(["uv","run","--locked","--group","dev","python","-m","scripts.local_operation"],env=live_env,timeout=150)
        code=live.returncode
        if code==0:
            (out/"live-result.json").write_text(json.dumps(json.loads(live.stdout),indent=2)+"\n",newline="\n")
            code=run([sys.executable,str(out/"verify-live.py")],env=env,timeout=45).returncode
finally:
    cleanup=run(compose+["down","--volumes","--remove-orphans"],timeout=120)
    after=inventory()
    (out/"inventory-after.json").write_text(json.dumps(after,indent=2)+"\n",newline="\n")
    preserved=all(set(before[k])<=set(after[k]) for k in before)
    remaining=run(["docker","ps","-a","-q","--filter","label=com.docker.compose.project="+namespace])
    report={"gate_exit_code":code,"cleanup_exit_code":cleanup.returncode,"prior_resources_preserved":preserved,"phase_containers_remaining":bool(remaining.stdout.strip())}
    (out/"service-result.json").write_text(json.dumps(report,indent=2)+"\n",newline="\n")
    print(json.dumps(report))
    if cleanup.returncode or not preserved or remaining.stdout.strip():
        code=1
sys.exit(code)
