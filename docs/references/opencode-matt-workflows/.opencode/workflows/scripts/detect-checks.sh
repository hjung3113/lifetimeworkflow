#!/usr/bin/env bash
set -euo pipefail
FORMAT=text FOCUS=;while [[ $# -gt 0 ]];do case "$1" in --format)FORMAT="${2:-text}";shift 2;;--focus)FOCUS="${2:-}";shift 2;;*)shift;;esac;done;if git rev-parse --is-inside-work-tree >/dev/null 2>&1;then cd "$(git rev-parse --show-toplevel)";fi
python3 - "$FORMAT" "$FOCUS" <<'PY'
import json,sys
from pathlib import Path
fmt,focus=sys.argv[1],sys.argv[2];r=Path.cwd();c=[]
def add(x,e,scope='full',confidence='high'):c.append({'command':x,'evidence':e,'scope':scope,'confidence':confidence})
if (r/'package.json').is_file():
 try:d=json.loads((r/'package.json').read_text());sc=d.get('scripts',{})
 except:sc={}
 pm='pnpm' if (r/'pnpm-lock.yaml').exists() else ('yarn' if (r/'yarn.lock').exists() else ('bun run' if (r/'bun.lockb').exists() or (r/'bun.lock').exists() else 'npm run'))
 for n in ('test','typecheck','check','lint','build'):
  if n in sc:add(f'{pm} {n}',f'package.json scripts.{n}')
pe=next((x for x in ['pytest.ini','tox.ini','noxfile.py','pyproject.toml'] if (r/x).is_file()),None)
if pe:
 t=(r/pe).read_text(errors='ignore')
 if pe!='pyproject.toml' or any(x in t for x in ('pytest','tool.pytest','pytest.ini_options')):add('python -m pytest',pe)
if (r/'Cargo.toml').is_file():add('cargo test','Cargo.toml')
if (r/'go.mod').is_file():add('go test ./...','go.mod')
if (r/'mvnw').is_file():add('./mvnw test','mvnw')
elif (r/'pom.xml').is_file():add('mvn test','pom.xml')
if (r/'gradlew').is_file():add('./gradlew test','gradlew')
sl=list(r.glob('*.sln'))
if sl:add('dotnet test',sl[0].name)
d={'schema':'detected-checks/v2','focus':focus or None,'checks':c,'note':'Candidates only. Repository instructions and task-specific seams override these suggestions.'}
if fmt=='json':print(json.dumps(d,indent=2))
else:
 print('suggested_checks:')
 for x in c:print(f"  - command: {x['command']}\n    evidence: {x['evidence']}\n    confidence: {x['confidence']}")
 print('note: '+d['note'])
PY
