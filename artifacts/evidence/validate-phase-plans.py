from pathlib import Path
import sys
root = Path('.')
phases = sorted((root / '.planning/phases').glob('*/PLAN.md'))
errors = []
for plan in phases:
    text = plan.read_text(encoding='utf-8')
    verify = plan.with_name('VERIFY.md')
    spec = plan.with_name('SPEC.md')
    tasks = [line for line in text.splitlines() if line.startswith(('1. ', '2. ', '3. ', '4. '))]
    for label, ok in [('SPEC', spec.exists()), ('VERIFY', verify.exists()), ('allowed paths', 'allowed_write_paths' in text), ('forbidden changes', 'forbidden_changes' in text), ('stop condition', 'stop' in text.lower())]:
        if not ok: errors.append(f'{plan}: missing {label}')
    if not 2 <= len(tasks) <= 4: errors.append(f'{plan}: {len(tasks)} tasks (expected 2-4)')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print(f'PASS: {len(phases)} phases each have SPEC/PLAN/VERIFY, 2-4 tasks, ownership, forbidden changes, and stop conditions')
