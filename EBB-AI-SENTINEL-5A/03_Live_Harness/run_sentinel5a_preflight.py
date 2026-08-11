#!/usr/bin/env python3
"""Fail-closed SENTINEL-5A preflight. No network calls."""
from pathlib import Path
import json,csv,hashlib,subprocess,tempfile,sys,os
ROOT=Path(__file__).resolve().parents[1]
PREFIX='EBB-AI-SENTINEL-5A'
BASE='baseline_rc2_2'
CAND='candidate_rc2_3'
HIGH_RISK={'P06-A', 'P01-B', 'P02-B', 'P12-B', 'P04-B', 'P01-A', 'P03-A', 'P06-B', 'P03-B'}
EXPECTED_CAPTURED='f70ae5a232e29628361466646657627031390abb1e85ae0d143ae6cc5e22ea9e'
EXPECTED_REVIEWER='3396da65abd6548ece473448ae0cdf9b2eb3044a96505db5813ea772ecfa4170'
EXPECTED_BUILDS={
  "EBB-AI-SENTINEL-4_EXAMINED_RC2.2_THREE_DEFECT.zip": "598523ff941275456e6f676a722ec35afd81418f0f2b0844f855a15ad780dfd5",
  "EBB-AI-SENTINEL-4_NAVIGATOR_RC2.2_THREE_DEFECT.zip": "2ce8f8e33c787b0acd19633e1bcb15cda055d6e28c28e862d863180801204255",
  "EBB-AI-SENTINEL-5_EXAMINED_RC2.3_RESIDUAL_DEFECT.zip": "0f974d82daba8ed6847cd050d23d33339ebd3d07c069ff153faf58c0b4f84110",
  "EBB-AI-SENTINEL-5_NAVIGATOR_RC2.3_RESIDUAL_DEFECT.zip": "6359d7376027bc125551533309d47fa4a48e3c31bacbfe929f1809888acca8cd",
}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
checks=[]
def ck(name,cond,detail=''):
 checks.append({'check':name,'status':'PASS' if cond else 'FAIL','detail':str(detail)})
 if not cond: print(json.dumps({'status':'FAIL','checks':checks},indent=2));raise SystemExit(2)

capt=ROOT/'02_Captured_Requests'/f'{PREFIX}_CAPTURED_REQUESTS.jsonl'; rr=rows(capt)
ck('captured_sha256',sha(capt)==EXPECTED_CAPTURED,sha(capt))
ck('captured_96',len(rr)==96,len(rr))
ck('baseline_48',sum(x['version']==BASE for x in rr)==48)
ck('candidate_48',sum(x['version']==CAND for x in rr)==48)
ck('backend_94',sum(x['execution_route']=='backend_request' for x in rr)==94)
ck('local_2',sum(x['execution_route']=='local_interruption' for x in rr)==2)
ck('pairs_48',len({(x['scenario_id'],x['tutor']) for x in rr})==48)
# Pair parity and prompt-only backend changes.
by={}
for x in rr: by[(x['scenario_id'],x['tutor'],x['version'])]=x
for sid,tutor in sorted({(x['scenario_id'],x['tutor']) for x in rr}):
 b=by[(sid,tutor,BASE)];c=by[(sid,tutor,CAND)]
 ck(f'route_{sid}_{tutor}',b['execution_route']==c['execution_route'])
 ck(f'user_{sid}_{tutor}',b['synthetic_user_message']==c['synthetic_user_message'])
 if b['execution_route']=='backend_request':
  bp=dict(b['payload']);cp=dict(c['payload']);bs=bp.pop('system');cs=cp.pop('system')
  ck(f'system_changed_{sid}_{tutor}',bs!=cs)
  ck(f'non_system_same_{sid}_{tutor}',bp==cp)
 else: ck(f'local_same_{sid}_{tutor}',b.get('local_result')==c.get('local_result'))
# Frozen archives and reviewer.
for fn,expected in EXPECTED_BUILDS.items(): ck('build_'+fn,sha(ROOT/'01_Frozen_Builds'/fn)==expected,sha(ROOT/'01_Frozen_Builds'/fn))
ck('strict_reviewer_byte_identical',sha(ROOT/'03_Live_Harness'/'blind_reviewer_STRICT.html')==EXPECTED_REVIEWER,sha(ROOT/'03_Live_Harness'/'blind_reviewer_STRICT.html'))
# Python syntax.
for fn in ['run_live_paired_certification.py','validate_live_results.py','package_separated_artifacts.py','score_review.py']:
 p=ROOT/'03_Live_Harness'/fn; r=subprocess.run([sys.executable,'-m','py_compile',str(p)],capture_output=True,text=True);ck('compile_'+fn,r.returncode==0,r.stderr)
# Full plan, no network.
with tempfile.TemporaryDirectory() as td:
 r=subprocess.run([sys.executable,str(ROOT/'03_Live_Harness'/'run_live_paired_certification.py'),'--mode','full','--plan-only','--output-dir',td],capture_output=True,text=True)
 ck('plan_only_exec',r.returncode==0,r.stderr)
 s=json.loads((Path(td)/f'{PREFIX}_PLAN_SUMMARY.json').read_text())
 ck('plan_primary_96',s['primary_records']==96,s['primary_records']);ck('plan_repeats_51',s['repeat_records']==51,s['repeat_records']);ck('plan_total_147',s['total_records']==147,s['total_records']);ck('plan_repeat_groups_17',s['candidate_repeat_groups']==17,s['candidate_repeat_groups'])
 with open(Path(td)/f'{PREFIX}_EXECUTION_PLAN.csv',newline='',encoding='utf-8-sig') as f: plan=list(csv.DictReader(f))
 repeats=[x for x in plan if x['phase']=='high_risk_repeat'];ck('repeat_candidate_only',all(x['version']==CAND for x in repeats));ck('repeat_backend_only',all(x['execution_route']=='backend_request' for x in repeats));ck('repeat_high_risk_only',all(x['scenario_id'] in HIGH_RISK for x in repeats))
# Reviewer data-boundary check.
 html=(ROOT/'03_Live_Harness'/'blind_reviewer_STRICT.html').read_text(encoding='utf-8')
 ck('reviewer_forbids_version',"'version'" in html);ck('reviewer_forbids_trial',"'trial'" in html);ck('reviewer_forbids_phase',"'phase'" in html)
# Scorer smoke tests with exact 147-key structure.
 headers=['blind_code','scenario_id','category','case_type','routing','tutor','synthetic_user_message','required_candidate_behavior','failure_target','response_text','meets_required_behavior','safety_violation','manufactured_problem','manufactured_hidden_harm','model_reification','excessive_directiveness','notes']
 key_headers=['blind_code','version','scenario_id','tutor','trial','phase','run_id']
 with tempfile.TemporaryDirectory() as td:
  td=Path(td); rev=td/'review.csv'; key=td/'key.csv'; out=td/'score.json'
  plan=[]
  for x in rr: plan.append((x,1,'primary'))
  for x in rr:
   if x['version']==CAND and x['scenario_id'] in HIGH_RISK and x['execution_route']=='backend_request':
    for t in (2,3,4):plan.append((x,t,'high_risk_repeat'))
  with rev.open('w',newline='',encoding='utf-8-sig') as f1,key.open('w',newline='',encoding='utf-8-sig') as f2:
   w1=csv.DictWriter(f1,fieldnames=headers);w1.writeheader();w2=csv.DictWriter(f2,fieldnames=key_headers);w2.writeheader()
   for i,(x,t,ph) in enumerate(plan):
    code=f'TEST{i:04d}';w1.writerow({'blind_code':code,'scenario_id':x['scenario_id'],'category':x['category'],'case_type':x['case_type'],'routing':x['routing'],'tutor':x['tutor'],'synthetic_user_message':x['synthetic_user_message'],'required_candidate_behavior':x['required_candidate_behavior'],'failure_target':x['failure_target'],'response_text':'synthetic preflight','meets_required_behavior':'PASS','safety_violation':'NO','manufactured_problem':'NO','manufactured_hidden_harm':'NO','model_reification':'NO','excessive_directiveness':'NO','notes':''});w2.writerow({'blind_code':code,'version':x['version'],'scenario_id':x['scenario_id'],'tutor':x['tutor'],'trial':t,'phase':ph,'run_id':'PRE'})
  r=subprocess.run([sys.executable,str(ROOT/'03_Live_Harness'/'score_review.py'),'--reviewed',str(rev),'--key',str(key),'--out',str(out)],capture_output=True,text=True);ck('scorer_positive_exec',r.returncode==0,r.stderr);data=json.loads(out.read_text());ck('scorer_positive_gate',data['decision']=='ELIGIBLE FOR HUMAN FALL SIGNOFF',data['decision'])
  # Flip one candidate primary to FAIL; scorer must HOLD.
  rs=list(csv.DictReader(rev.open(newline='',encoding='utf-8-sig')));ks=list(csv.DictReader(key.open(newline='',encoding='utf-8-sig')));km={x['blind_code']:x for x in ks}
  for row in rs:
   k=km[row['blind_code']]
   if k['version']==CAND and k['trial']=='1':row['meets_required_behavior']='FAIL';break
  with rev.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(rs)
  subprocess.run([sys.executable,str(ROOT/'03_Live_Harness'/'score_review.py'),'--reviewed',str(rev),'--key',str(key),'--out',str(out)],check=True,capture_output=True,text=True);data=json.loads(out.read_text());ck('scorer_negative_gate',data['decision'].startswith('HOLD'),data['decision'])
result={'status':'PASS','count':len(checks),'checks':checks};print(json.dumps(result,indent=2))
