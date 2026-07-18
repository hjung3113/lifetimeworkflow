#!/usr/bin/env bash
set -euo pipefail
SKILLS= REQUIRE=tracker,domain FORMAT=text; LEGACY=()
while [[ $# -gt 0 ]]; do case "$1" in --skills) SKILLS="${2:-}";shift 2;;--require) REQUIRE="${2:-none}";shift 2;;--format) FORMAT="${2:-text}";shift 2;;*) LEGACY+=("$1");shift;;esac;done
[[ -z "$SKILLS" && ${#LEGACY[@]} -gt 0 ]] && SKILLS="$(IFS=,;echo "${LEGACY[*]}")"; if git rev-parse --is-inside-work-tree >/dev/null 2>&1;then cd "$(git rev-parse --show-toplevel)";fi
python3 - "$SKILLS" "$REQUIRE" "$FORMAT" <<'PY'
import json,sys
from pathlib import Path
skills=[x for x in sys.argv[1].split(',') if x]; req=[] if sys.argv[2] in ('','none') else [x for x in sys.argv[2].split(',') if x]; fmt=sys.argv[3]; r=Path.cwd(); h=Path.home(); roots=[r/'.opencode/skills',r/'.claude/skills',r/'.agents/skills',h/'.config/opencode/skills',h/'.claude/skills',h/'.agents/skills'];found={};missing=[]
for s in skills:
 p=next((x/s/'SKILL.md' for x in roots if (x/s/'SKILL.md').is_file()),None)
 if p:found[s]=str(p)
 else:missing.append(s)
checks={'tracker':r/'docs/agents/issue-tracker.md','domain':r/'docs/agents/domain.md','progress':r/'.workflow/PROGRESS.md'}; ms=[x for x in req if x in checks and not checks[x].is_file()]; status='ok' if not missing and not ms else 'fail'; nxt='npx skills@latest add mattpocock/skills' if missing else ('/flow-setup' if any(x in ms for x in ('tracker','domain')) else ('/flow-progress initialise progress' if ms else None)); d={'schema':'workflow-preflight/v2','status':status,'skills':found,'missing_skills':missing,'required_setup':req,'missing_setup':ms,'next_action':nxt}
if fmt=='json':print(json.dumps(d,indent=2))
else:
 [print(f'skill:{k}={v}') for k,v in found.items()];print('missing_skills='+','.join(missing));print('missing_setup='+','.join(ms));print('next='+(nxt or 'none'));print('STATUS='+status.upper())
PY
