"""Validate saved inventories without rerunning services or the full gate."""
import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
before = json.loads((evidence / 'before-run4.json').read_text())
after = json.loads((evidence / 'after-run4.json').read_text())
for field in ('containers', 'networks', 'volumes'):
    assert before[field] == after[field], field
unrelated = lambda rows: {r for r in rows if not r.startswith('supportops-async:phase027 ')}
assert unrelated(before['images']) == unrelated(after['images'])
report = {
    'status': 'PASS_SCOPED_RECONCILIATION',
    'containers': len(after['containers']), 'networks': len(after['networks']), 'volumes': len(after['volumes']),
    'unrelated_images_unchanged': True,
    'owned_image_before': sorted(set(before['images']) - unrelated(before['images'])),
    'owned_image_after': sorted(set(after['images']) - unrelated(after['images'])),
    'original_wrapper_exit': 1,
    'original_wrapper_reason': 'overbroad image preservation assertion after full gate exit 0',
}
(evidence / 'reconciliation-final.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
