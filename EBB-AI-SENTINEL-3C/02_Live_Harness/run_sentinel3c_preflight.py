#!/usr/bin/env python3
"""SENTINEL-3C execution preflight: identities, captured requests, strict reviewer, scripts, and 147-record plan."""
from pathlib import Path
import hashlib,json,csv,subprocess,sys,re,tempfile,shutil,os

here=Path(__file__).resolve().parent
root=here.parent
PREFIX='EBB-AI-SENTINEL-3C'
expected={
 'EBB-AI-SENTINEL-2_EXAMINED_RC2_FROZEN_CANDIDATE.zip':'8cef138c4407923df638b127a60d9a0d463b044fd96b87b062761d599591f00f',
 'EBB-AI-SENTINEL-2_NAVIGATOR_RC2_FROZEN_CANDIDATE.zip':'09e215fec74b6f6850b5fa943032c3252a3198198eeb49bdf84483f1e4e62303',
 'EBB-AI-SENTINEL-3_EXAMINED_RC2.1_FAILURE_LOCALIZED.zip':'fde71485742c3f62e0853a6fb62f52c1c37d79dff16ff8126a26098b6310f433',
 'EBB-AI-SENTINEL-3_NAVIGATOR_RC2.1_FAILURE_LOCALIZED.zip':'49b33e56524441c8c4deaf1f8ac6c420ea5ed19e179bab8d1d02e5f68ffc991d',
}
checks=[]
def add(name,ok,detail=''): checks.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

for name,digest in expected.items():
    p=root/'00_Frozen_Builds'/name
    add('hash_'+name,p.exists() and sha(p)==digest,sha(p) if p.exists() else 'MISSING')

captured=root/'01_Captured_Requests'/f'{PREFIX}_CAPTURED_REQUESTS.jsonl'
rows=[json.loads(x) for x in captured.read_text(encoding='utf-8').splitlines() if x.strip()]
add('captured_96',len(rows)==96,str(len(rows)))
add('captured_baseline_48',sum(r.get('version')=='baseline_rc2' for r in rows)==48,'')
add('captured_candidate_48',sum(r.get('version')=='candidate_rc2_1' for r in rows)==48,'')
add('captured_routes_94_backend_2_local',
    sum(r.get('execution_route')=='backend_request' for r in rows)==94 and
    sum(r.get('execution_route')=='local_interruption' for r in rows)==2,'')

reviewer=(here/'blind_reviewer_STRICT.html').read_text(encoding='utf-8')
add('reviewer_forbidden_version_trial_phase',
    "const forbidden=['version','trial','phase']" in reviewer,'')
add('reviewer_3c_namespace','EBB-AI-SENTINEL-3C' in reviewer,'')

for script in ['run_live_paired_certification.py','validate_live_results.py','package_separated_artifacts.py','score_review.py']:
    p=here/script
    cp=subprocess.run([sys.executable,'-m','py_compile',str(p)],capture_output=True,text=True)
    add('compile_'+script,cp.returncode==0,cp.stderr.strip())

tmp=Path(tempfile.mkdtemp(prefix='sentinel3c-plan-'))
try:
    cp=subprocess.run([sys.executable,str(here/'run_live_paired_certification.py'),'--mode','full','--plan-only','--output-dir',str(tmp)],
                      capture_output=True,text=True)
    add('plan_only_runner_exit',cp.returncode==0,cp.stderr.strip())
    summary=json.loads((tmp/f'{PREFIX}_PLAN_SUMMARY.json').read_text(encoding='utf-8')) if (tmp/f'{PREFIX}_PLAN_SUMMARY.json').exists() else {}
    add('plan_primary_96',summary.get('primary_records')==96,str(summary.get('primary_records')))
    add('plan_repeats_51',summary.get('repeat_records')==51,str(summary.get('repeat_records')))
    add('plan_total_147',summary.get('total_records')==147,str(summary.get('total_records')))
    add('plan_groups_17',summary.get('candidate_repeat_groups')==17,str(summary.get('candidate_repeat_groups')))
finally:
    shutil.rmtree(tmp,ignore_errors=True)

ok=all(x['status']=='PASS' for x in checks)
outj=root/'04_QA'/f'{PREFIX}_PREFLIGHT_RESULTS.json'
outc=root/'04_QA'/f'{PREFIX}_PREFLIGHT_RESULTS.csv'
outj.write_text(json.dumps({'status':'PASS' if ok else 'FAIL','checks':checks},indent=2),encoding='utf-8')
with outc.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['check','status','detail']);w.writeheader();w.writerows(checks)
print(json.dumps({'status':'PASS' if ok else 'FAIL','checks':checks},indent=2))
if not ok:raise SystemExit(2)
