#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); problems=[]
for p in ['.opencode/agents/flow-orchestrator.md','.opencode/agents/flow-adversarial-review.md','.opencode/workflows/scripts/workflow-progress.py','.opencode/workflows/scripts/adversarial-review.py']:
 if not (root/p).is_file():problems.append('missing '+p)
try: subprocess.run(['opencode','--version'],capture_output=True,check=True);opencode=True
except:opencode=False
print(json.dumps({'status':'ok' if not problems else 'fail','root':str(root),'problems':problems,'opencode_cli':opencode,'next':'opencode debug config' if opencode else 'install OpenCode CLI, then run opencode debug config'},indent=2));sys.exit(0 if not problems else 1)
