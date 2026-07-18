#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-.}"; SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; TARGET="$(mkdir -p "$TARGET" && cd "$TARGET" && pwd)"; STAMP="$(date +%Y%m%d%H%M%S)"; MANIFEST="$TARGET/.opencode/workflows/install-manifest.json"; BACKUP="$TARGET/.opencode/workflows/backups/$STAMP"; mkdir -p "$BACKUP"
python3 - "$SOURCE_DIR" "$TARGET" "$MANIFEST" "$BACKUP" <<'PY'
import hashlib,json,shutil,sys
from pathlib import Path
src,target,manifest,backup=map(Path,sys.argv[1:]); files=[p for p in (src/'.opencode').rglob('*') if p.is_file()]+[src/'UPSTREAM_SKILLS.md',src/'ADVERSARIAL_REVIEW_DESIGN.md',src/'ADVERSARIAL_REVIEW_TEMPLATES.md',src/'SCRIPT_REVIEW_IMPLEMENTATION.md']; new={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}; old={}
if manifest.exists():
 try:old=json.loads(manifest.read_text()).get('files',{})
 except:old={}
for rel,oldhash in old.items():
 if rel in new:continue
 dst=target/rel
 if dst.is_file():
  current=hashlib.sha256(dst.read_bytes()).hexdigest()
  if current!=oldhash:
   b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,b)
  dst.unlink()
for p in files:
 rel=str(p.relative_to(src));dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest()!=new[rel]:
  b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,b)
 shutil.copy2(p,dst)
manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps({'schema':'opencode-workflow-install/v1','files':new},indent=2)+'\n')
PY
chmod +x "$TARGET/.opencode/workflows/scripts/"*.sh "$TARGET/.opencode/workflows/scripts/"*.py "$TARGET/.opencode/workflows/configure-models.py" 2>/dev/null || true
find "$BACKUP" -type f | grep -q . || rmdir "$BACKUP" 2>/dev/null || true
echo "Installed OpenCode workflows into: $TARGET"; echo "Next: install upstream skills, run /flow-setup, then python3 '$SOURCE_DIR/verify-bundle.py' && python3 '$SOURCE_DIR/doctor.py' '$TARGET'"
