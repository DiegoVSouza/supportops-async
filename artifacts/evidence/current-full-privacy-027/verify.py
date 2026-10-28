"""Run the approved isolated local gate and reconcile Docker ownership."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
records = []
previous = evidence / 'before-containers-attempt2.txt'
if previous.exists() and '"Status"' in previous.read_text():
    clean = []
    for line in previous.read_text().splitlines():
        identity, name, image, status, state, labels = line.split('|')
        clean.append('|'.join([identity, name, image, status, json.dumps(json.loads(state).get('Health', {}).get('Status')), json.dumps((json.loads(labels) or {}).get('com.docker.compose.project'))]))
    previous.write_text('\n'.join(clean) + '\n')

def run(args, label, *, timeout=60, env=None, check=True):
    result = subprocess.run(args, cwd=root, env=env, capture_output=True, timeout=timeout)
    output = result.stdout + result.stderr
    (evidence / (label + '-run4.txt')).write_bytes(output)
    records.append({'command': args, 'cwd': str(root), 'exit_code': result.returncode, 'output': label + '-run4.txt'})
    (evidence / 'commands-run4.json').write_text(json.dumps(records, indent=2))
    if check and result.returncode:
        raise RuntimeError(label + '_failed')
    return result

def snapshot(label):
    ids = run(['docker', 'container', 'ls', '-aq', '--no-trunc'], label + '-ids').stdout.decode().split()
    template = '{{.Id}}|{{.Name}}|{{.Image}}|{{.State.Status}}|{{with index .State "Health"}}{{index . "Status"}}{{end}}|{{index .Config.Labels "com.docker.compose.project"}}'
    inspected = run(['docker', 'inspect', '--format', template, *ids], label + '-containers').stdout.decode().splitlines()
    containers = {}
    for line in inspected:
        identity, name, image, status, health, project = line.split('|')
        containers[identity] = [name, image, status, health, project]
    networks = run(['docker', 'network', 'ls', '--format', '{{.ID}} {{.Name}}'], label + '-networks').stdout.decode().splitlines()
    volumes = run(['docker', 'volume', 'ls', '--format', '{{.Name}}'], label + '-volumes').stdout.decode().splitlines()
    images = run(['docker', 'image', 'ls', '--no-trunc', '--format', '{{.Repository}}:{{.Tag}} {{.ID}}'], label + '-images').stdout.decode().splitlines()
    result = {'containers': containers, 'networks': sorted(networks), 'volumes': sorted(volumes), 'images': sorted(images)}
    (evidence / (label + '.json')).write_text(json.dumps(result, indent=2))
    return result

run(['docker', 'info', '--format', '{{.ServerVersion}}'], 'docker-version')
before = snapshot('before-run4')
assert not any(c[-1] == 'p04-phase027' for c in before['containers'].values())
assert not any('p04-phase027' in n for n in before['networks'] + before['volumes'])
prior = json.loads((evidence / 'reconciliation.json').read_text())
assert all(i in prior['new_images'] for i in before['images'] if i.startswith('supportops-async:phase027 '))
for port in (35432, 34566, 36379):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', port))
for image in ('postgres:17.11-alpine3.24', 'localstack/localstack:4.14.0', 'redis@sha256:becdda6c7f4b3fb42e42fd7f120bbf5c54c4caaaf16f26da24e4563d2c1f0576', 'hashicorp/terraform:1.16.6'):
    run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], 'image-' + str(len(records)))
work = evidence / 'work-run4'
work.mkdir()
for source in (root / 'infra/terraform').iterdir():
    if source.suffix == '.tf' or source.name == '.terraform.lock.hcl':
        shutil.copyfile(source, work / source.name)
(evidence / 'terraform-run4.rc').write_text('provider_installation {\n  filesystem_mirror {\n    path = "/mirror"\n    include = ["registry.terraform.io/hashicorp/aws"]\n  }\n}\n')
compose = ['docker', 'compose', '-p', 'p04-phase027', '-f', str(evidence / 'compose.yml')]
run(compose + ['config', '--quiet'], 'compose-config')
env = os.environ | {
    'LLM_MODE': 'fake', 'P04_POSTGRES_DSN': 'postgresql://supportops:supportops@127.0.0.1:35432/supportops',
    'P04_LOCALSTACK_ENDPOINT': 'http://127.0.0.1:34566', 'P04_TEST_REDIS_URL': 'redis://127.0.0.1:36379/0',
    'P04_PYTEST_BASETEMP': str(evidence.relative_to(root) / 'tmp-run4'),
    'PYTHONPATH': str(root),
    'P04_CHECK_IMAGE_TAG': 'supportops-async:phase027',
    'P04_TERRAFORM_WORKSPACE': str(work.relative_to(root)),
    'P04_TERRAFORM_MIRROR': str(root / 'infra/terraform/.terraform/providers'),
    'P04_TERRAFORM_CLI_CONFIG': str(evidence / 'terraform-run4.rc'),
    'P04_TERRAFORM_NETWORK': 'p04-phase027-local', 'P04_TERRAFORM_ENDPOINT': 'http://localstack:4566',
}
try:
    run(compose + ['up', '-d', '--pull', 'never', '--wait', '--wait-timeout', '150'], 'up', timeout=180)
    owned = run(compose + ['ps', '-q'], 'owned-ids').stdout.decode().split()
    for identity in owned:
        run(['docker', 'inspect', identity, '--format', '{{json .Mounts}}'], 'mounts-' + identity[:12])
    gate = run(['uv', 'run', '--locked', '--offline', 'python', 'scripts/check_full.py'], 'full-attempt2', timeout=600, env=env, check=False)
finally:
    run(compose + ['down', '--volumes', '--remove-orphans'], 'cleanup', timeout=90)
    after = snapshot('after-run4')
    comparison = {'containers_preserved': before['containers'] == after['containers'], 'networks_preserved': before['networks'] == after['networks'], 'volumes_preserved': before['volumes'] == after['volumes'], 'old_images_preserved': set(before['images']) <= set(after['images']), 'new_images': sorted(set(after['images']) - set(before['images']))}
    (evidence / 'reconciliation-run4.json').write_text(json.dumps(comparison, indent=2))
unrelated_before = {i for i in before['images'] if not i.startswith('supportops-async:phase027 ')}
unrelated_after = {i for i in after['images'] if not i.startswith('supportops-async:phase027 ')}
assert unrelated_before == unrelated_after
assert all(comparison[k] for k in ('containers_preserved', 'networks_preserved', 'volumes_preserved'))
sys.exit(gate.returncode)
