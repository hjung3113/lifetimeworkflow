#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,re,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
def root():
 try:return Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True,stderr=subprocess.DEVNULL).strip())
 except:return Path.cwd()
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')[:60] or 'review'
def atom(p,t):
 p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.',suffix='.tmp')
 with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(t)
 os.replace(tmp,p)
def ws(i):return root()/'.workflow/reviews'/i
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
 i=sp.add_parser('init');i.add_argument('--title',required=True);i.add_argument('--case',choices=['design','code','document','debug','refactor','api-data'],required=True);i.add_argument('--target',required=True);i.add_argument('--objective',required=True);i.add_argument('--done',required=True);i.add_argument('--risk',choices=['high','critical'],default='high');i.add_argument('--review-id')
 s=sp.add_parser('status');s.add_argument('review_id');s.add_argument('--json',action='store_true')
 rf=sp.add_parser('record-finding');rf.add_argument('review_id');rf.add_argument('--id',required=True);rf.add_argument('--severity',choices=['critical','high','medium','low'],required=True);rf.add_argument('--file',required=True)
 rc=sp.add_parser('record-challenge');rc.add_argument('review_id');rc.add_argument('--finding',required=True);rc.add_argument('--verdict',choices=['uphold','narrow','reject','needs-evidence'],required=True);rc.add_argument('--file',required=True)
 fn=sp.add_parser('finalize');fn.add_argument('review_id');fn.add_argument('--file',required=True)
 v=sp.add_parser('validate');v.add_argument('review_id');a=p.parse_args()
 if a.cmd=='init':
  rid=a.review_id or datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+slug(a.title);d=ws(rid);d.mkdir(parents=True,exist_ok=True);(d/'reviews').mkdir(exist_ok=True);(d/'challenges').mkdir(exist_ok=True)
  state={'schema':'adversarial-review/v1','review_id':rid,'title':a.title,'case':a.case,'target':a.target,'objective':a.objective,'definition_of_done':a.done,'risk':a.risk,'status':'chartered','created_at':now()};atom(d/'state.json',json.dumps(state,indent=2));atom(d/'00-CHARTER.md',f'# Review Charter\n\n- **Review ID:** {rid}\n- **Case:** {a.case}\n- **Risk:** {a.risk}\n- **Target:** {a.target}\n- **Objective:** {a.objective}\n- **Definition of done:** {a.done}\n\n## Evidence Pack\n\nObserved facts only. Mark unknowns explicitly.\n\n## Scope\n\n## Non-goals\n\n## Decision Criteria\n\n## Selected Experts\n')
  atom(d/'FINDING_TEMPLATE.md','# Finding <ROLE>-<NN>\n\n- **Claim:**\n- **Severity:** critical | high | medium | low\n- **Confidence:** high | medium | low\n- **Evidence:**\n- **Affected area:**\n- **Failure scenario:**\n- **Recommended action:**\n- **Falsification condition:**\n- **Disposition:** pending\n');atom(d/'CHALLENGE_TEMPLATE.md','# Challenge for <FINDING-ID>\n\n- **Verdict:** uphold | narrow | reject | needs-evidence\n- **Strongest counterargument:**\n- **Evidence checked:**\n- **Hidden assumption:**\n- **Severity correction:**\n- **Required revision:**\n');atom(d/'FINAL_TEMPLATE.md','# Adversarial Review Synthesis\n\n## Verdict\n\n## Accepted Findings\n\n## Rejected or Narrowed Findings\n\n## Deferred Unknowns\n\n## Required Reinforcement\n\n## Recommended Reinforcement\n\n## Residual Risk\n\n## Case-specific Output\n\n## Continuity Candidates\n\n## Next Workflow\n');print(rid);return
 d=ws(a.review_id)
 if not d.exists():raise SystemExit('unknown review')
 if a.cmd=='status':
  x=json.loads((d/'state.json').read_text());x['files']=sorted(str(q.relative_to(d)) for q in d.rglob('*') if q.is_file());print(json.dumps(x,indent=2) if a.json else '\n'.join(x['files']));return
 state=json.loads((d/'state.json').read_text())
 if a.cmd=='record-finding':
  state.setdefault('findings',{})[a.id]={'severity':a.severity,'file':a.file};atom(d/'state.json',json.dumps(state,indent=2));return
 if a.cmd=='record-challenge':
  state.setdefault('challenges',{})[a.finding]={'verdict':a.verdict,'file':a.file};atom(d/'state.json',json.dumps(state,indent=2));return
 if a.cmd=='finalize':
  src=d/a.file
  if not src.is_file():raise SystemExit('final file missing')
  if src.name!='FINAL.md':atom(d/'FINAL.md',src.read_text())
  state['status']='completed';state['final_file']='FINAL.md';atom(d/'state.json',json.dumps(state,indent=2));return
 errs=[]
 for f in ['00-CHARTER.md','state.json','FINAL.md']:
  if not (d/f).is_file():errs.append('missing '+f)
 reviews=list((d/'reviews').glob('*.md'));ch=list((d/'challenges').glob('*.md'))
 if len(reviews)<3:errs.append('fewer than 3 independent reviews')
 if not ch:errs.append('no finding challenges')
 findings=state.get('findings',{});challenges=state.get('challenges',{})
 for fid,f in findings.items():
  if f.get('severity') in ('critical','high') and fid not in challenges:errs.append('unchallenged '+fid)
 if not findings:errs.append('no normalized findings registered')
 print(json.dumps({'status':'ok' if not errs else 'fail','errors':errs,'review_files':len(reviews),'challenge_files':len(ch)},indent=2));raise SystemExit(0 if not errs else 2)
if __name__=='__main__':main()
