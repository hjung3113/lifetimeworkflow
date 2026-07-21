#!/usr/bin/env python3
from pathlib import Path
import re,sys,yaml
root=Path(__file__).resolve().parent; agents=root/'.opencode/agents';commands=root/'.opencode/commands';errors=[]
def parse(p):
 t=p.read_text();m=re.match(r'^---\n(.*?)\n---\n',t,re.S)
 if not m:raise ValueError('missing frontmatter')
 return yaml.safe_load(m.group(1)),t[m.end():]
A={}
for p in agents.glob('*.md'):
 try:d,b=parse(p);A[p.stem]=d
 except Exception as e:errors.append(f'{p}: {e}');continue
 if d.get('permission',{}).get('*')!='deny':errors.append(f'{p}: not default deny')
 if p.stem!='flow-orchestrator' and d.get('mode')!='subagent':errors.append(f'{p}: not subagent')
 if p.stem=='flow-orchestrator' and d.get('mode')!='primary':errors.append('orchestrator not primary')
 if p.stem.startswith('flow-adversarial-') and p.stem!='flow-adversarial-review' and d.get('hidden') is not True:errors.append(f'{p}: expert not hidden')
 if p.stem.startswith('flow-adversarial-') and d.get('edit',None):pass
C={}
for p in commands.glob('*.md'):
 try:d,b=parse(p);C[p.stem]=d
 except Exception as e:errors.append(f'{p}: {e}');continue
 if d.get('agent') not in A:errors.append(f'{p}: missing agent {d.get("agent")}')
 if '$ARGUMENTS' not in b:errors.append(f'{p}: arguments not preserved')
for n in ['repo-context.sh','workflow-preflight.sh','detect-checks.sh','workflow-progress.py','adversarial-review.py']:
 if not (root/'.opencode/workflows/scripts'/n).exists():errors.append('missing script '+n)
coord=A.get('flow-adversarial-review',{}).get('permission',{}).get('task',{})
expected={f'flow-adversarial-{x}' for x in ['alignment','architecture','verification','impact','diagnosis','migration','challenge','synthesis']}
allowed={k for k,v in coord.items() if k!='*' and v=='allow'}
if allowed!=expected:errors.append('adversarial coordinator allowlist mismatch')
orch=A.get('flow-orchestrator',{}).get('permission',{}).get('task',{})
if orch.get('flow-adversarial-review')!='allow':errors.append('orchestrator cannot call adversarial review')
if errors:
 print('\n'.join('ERROR: '+e for e in errors));sys.exit(1)
print(f'Validated {len(A)} agents and {len(C)} commands. Permissions, references, adversarial isolation, and helpers: OK')
