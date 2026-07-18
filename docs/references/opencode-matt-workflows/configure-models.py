#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,shutil
from pathlib import Path
MODEL_RE=re.compile(r'^[^/\s]+/[^\s]+$'); FRONT_RE=re.compile(r'\A---\n(.*?)\n---\n',re.S)
def planned(path,model):
 text=path.read_text();m=FRONT_RE.match(text)
 if not m:raise ValueError(f'missing frontmatter: {path}')
 lines=[x for x in m.group(1).splitlines() if not x.startswith('model:')]
 if model:
  if not MODEL_RE.match(model):raise ValueError(f'invalid model id {model!r}')
  i=next((i+1 for i,x in enumerate(lines) if x.startswith('mode:')),1);lines.insert(i,f'model: {model}')
 return '---\n'+'\n'.join(lines)+'\n---\n'+text[m.end():]
def main():
 p=argparse.ArgumentParser();p.add_argument('config',type=Path);p.add_argument('target',type=Path,nargs='?',default=Path('.'));p.add_argument('--dry-run',action='store_true');p.add_argument('--backup',action='store_true');a=p.parse_args();c=json.loads(a.config.read_text());tiers=c.get('tiers',{});ats=c.get('agent_tiers',{});ao=c.get('agent_overrides',{});co=c.get('command_overrides',{});ad=a.target/'.opencode/agents';cd=a.target/'.opencode/commands';agents={x.stem:x for x in ad.glob('flow-*.md')};commands={x.stem:x for x in cd.glob('flow*.md')};unknown=(set(ao)|set(ats))-set(agents);unknown_c=set(co)-set(commands)
 if unknown or unknown_c:raise SystemExit(f'Unknown definitions: agents={sorted(unknown)}, commands={sorted(unknown_c)}')
 changes=[]
 for n,path in sorted(agents.items()):
  model=ao.get(n,tiers.get(ats.get(n,''),'') or None);new=planned(path,model)
  if new!=path.read_text():changes.append((path,new,model))
 for n,model in co.items():
  path=commands[n];new=planned(path,model or None)
  if new!=path.read_text():changes.append((path,new,model or None))
 for path,new,model in changes:
  print(f'{path.stem}: -> {model or "inherit"}')
  if not a.dry_run:
   if a.backup:shutil.copy2(path,path.with_suffix(path.suffix+'.bak'))
   path.write_text(new)
 print(f'{"Would update" if a.dry_run else "Updated"} {len(changes)} definitions')
if __name__=='__main__':main()
