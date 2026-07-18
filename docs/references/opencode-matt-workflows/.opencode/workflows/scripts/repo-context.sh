#!/usr/bin/env bash
set -euo pipefail
MODE=routing FOCUS= FORMAT=text MAX_ITEMS=40
while [[ $# -gt 0 ]]; do case "$1" in --routing|--implementation|--review) MODE="${1#--}"; shift;; --focus) FOCUS="${2:-}"; shift 2;; --format) FORMAT="${2:-text}"; shift 2;; --max-items) MAX_ITEMS="${2:-40}"; shift 2;; *) shift;; esac; done
INVOKED_FROM="$PWD"; if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT="$(git rev-parse --show-toplevel)"; else ROOT="$PWD"; fi; cd "$ROOT"
python3 - "$MODE" "$FOCUS" "$FORMAT" "$MAX_ITEMS" "$INVOKED_FROM" <<'PY'
import json,subprocess,sys
from pathlib import Path
mode,focus,fmt,max_items,invoked=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),sys.argv[5]; root=Path.cwd()
def run(*a):
 try:return subprocess.check_output(a,text=True,stderr=subprocess.DEVNULL).strip()
 except:return ''
def exists(xs):return [x for x in xs if (root/x).exists()]
s={'schema':'repo-context/v2','mode':mode,'invoked_from':invoked,'root':str(root),'git':{},'workflow_setup':{},'manifests':[],'top_level':[],'focus':{'requested':focus or None,'candidate_paths':[]},'evidence_budget':{'max_items':max_items}}
if run('git','rev-parse','--is-inside-work-tree')=='true':s['git']={'branch':run('git','branch','--show-current') or 'DETACHED','head':run('git','rev-parse','--short','HEAD') or 'unknown','status':run('git','status','--short','--branch').splitlines()[:20],'recent_commits':run('git','log','-5','--oneline').splitlines()}
setup=['AGENTS.md','CLAUDE.md','docs/agents/issue-tracker.md','docs/agents/domain.md','docs/agents/triage-labels.md','CONTEXT.md','CONTEXT-MAP.md']; s['workflow_setup']={x:True for x in exists(setup)}
mans=['package.json','pnpm-workspace.yaml','yarn.lock','pnpm-lock.yaml','package-lock.json','bun.lockb','bun.lock','pyproject.toml','requirements.txt','Cargo.toml','go.mod','pom.xml','build.gradle','build.gradle.kts']; s['manifests']=exists(mans)+[p.name for p in root.glob('*.sln')]
exclude={'.git','node_modules','.venv','dist','build','.next','target'}; s['top_level']=sorted(p.name for p in root.iterdir() if p.name not in exclude)[:max_items]
if focus:
 p=root/focus
 if p.exists():s['focus']['candidate_paths'].append(str(p.relative_to(root)))
 terms=[t.lower() for t in focus.replace('/',' ').replace('-',' ').replace('_',' ').split() if len(t)>2][:5]; out=[]
 for base in ['src','app','packages','docs','tests','test']:
  bp=root/base
  if not bp.exists():continue
  for p in bp.rglob('*'):
   rel=str(p.relative_to(root))
   if any(t in rel.lower() for t in terms):out.append(rel)
   if len(out)>=8:break
 s['focus']['candidate_paths'] += [x for x in out if x not in s['focus']['candidate_paths']]
if mode=='review' and s['git']:s['review']={'changed_files':run('git','diff','--name-only').splitlines()[:max_items],'staged_files':run('git','diff','--cached','--name-only').splitlines()[:max_items]}
if fmt=='json':print(json.dumps(s,ensure_ascii=False,indent=2))
else:
 print(f"schema: {s['schema']}\nmode: {mode}\nroot: {root}\nbranch: {s['git'].get('branch','not-a-worktree')}\nhead: {s['git'].get('head','unknown')}")
 for k in ['workflow_setup','manifests','top_level']:
  print(k+':'); vals=s[k].keys() if isinstance(s[k],dict) else s[k]
  for x in vals:print('  - '+x)
 if focus:
  print('focus_candidates:');[print('  - '+x) for x in s['focus']['candidate_paths']]
PY
