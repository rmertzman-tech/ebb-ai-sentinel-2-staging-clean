#!/usr/bin/env python3
"""Create non-overlapping strict blind and custodian ZIPs after successful SENTINEL-4A validation."""
from pathlib import Path
import argparse,zipfile,hashlib,json,csv,shutil,os

PREFIX='EBB-AI-SENTINEL-4A'
FORBIDDEN_NAMES=('BLIND_KEY','LIVE_RESPONSES','CHECKPOINT','EXECUTION_PLAN','backend_reachability','score_review')
FORBIDDEN_FIELDS={'version','trial','phase','run_index','endpoint','model','execution_route','raw_response','run_id'}

p=argparse.ArgumentParser()
p.add_argument('--results-dir',required=True)
p.add_argument('--harness-dir',required=True)
p.add_argument('--out-dir',required=True)
a=p.parse_args()
results=Path(a.results_dir); harness=Path(a.harness_dir); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

validation=results/f'{PREFIX}_POSTRUN_VALIDATION.json'
if not validation.exists() or json.loads(validation.read_text(encoding='utf-8')).get('status')!='PASS':
    raise SystemExit('Post-run validation must PASS before packaging.')

blind_json=results/f'{PREFIX}_BLIND_REVIEW_INPUT.json'
reviewer=harness/'blind_reviewer_STRICT.html'
blind_records=json.loads(blind_json.read_text(encoding='utf-8'))
for i,r in enumerate(blind_records,1):
    leak=FORBIDDEN_FIELDS & set(r)
    if leak: raise SystemExit(f'Blind record {i} leaks fields: {sorted(leak)}')

blind_readme=out/'README_BLIND_ONLY.txt'
blind_readme.write_text(
    'SENTINEL-4A STRICT BLIND REVIEW ARTIFACT\\n'
    'This artifact intentionally contains no version, trial, phase, run ID, endpoint, model, execution-route, or custodian key.\\n'
    'Complete and lock all 147 judgments before obtaining the separate custodian artifact.\\n',
    encoding='utf-8'
)
blind_manifest=out/'BLIND_ARTIFACT_MANIFEST.txt'
blind_manifest.write_text(
    f'{blind_json.name}  SHA256 {sha256(blind_json)}\\n'
    f'{reviewer.name}  SHA256 {sha256(reviewer)}\\n'
    f'{blind_readme.name}  SHA256 {sha256(blind_readme)}\\n',
    encoding='utf-8'
)
blind_zip=out/'sentinel4a-blind-review.zip'
with zipfile.ZipFile(blind_zip,'w',compression=zipfile.ZIP_DEFLATED) as z:
    z.write(blind_json,blind_json.name)
    z.write(reviewer,reviewer.name)
    z.write(blind_readme,blind_readme.name)
    z.write(blind_manifest,blind_manifest.name)

# Re-open and fail on suspicious names.
with zipfile.ZipFile(blind_zip) as z:
    names=z.namelist()
    for n in names:
        if any(token.lower() in n.lower() for token in FORBIDDEN_NAMES):
            raise SystemExit(f'Forbidden custodian-like filename in blind ZIP: {n}')
    # inspect JSON again from inside ZIP
    data=json.loads(z.read(blind_json.name).decode('utf-8'))
    if any(FORBIDDEN_FIELDS & set(r) for r in data):
        raise SystemExit('Forbidden hidden field detected inside blind ZIP.')

custodian_files=[
    results/f'{PREFIX}_BLIND_KEY.csv',
    results/f'{PREFIX}_LIVE_RESPONSES.csv',
    results/f'{PREFIX}_LIVE_RESPONSES.jsonl',
    results/'LIVE_RESPONSES_CHECKPOINT.jsonl',
    results/f'{PREFIX}_LIVE_RUN_SUMMARY.json',
    results/f'{PREFIX}_EXECUTION_PLAN.csv',
    results/'backend_reachability.json',
    results/f'{PREFIX}_POSTRUN_VALIDATION.json',
    results/f'{PREFIX}_POSTRUN_VALIDATION.csv',
    harness/'score_review.py'
]
for f in custodian_files:
    if not f.exists(): raise SystemExit(f'Missing custodian file: {f}')
cust_manifest=out/'CUSTODIAN_ARTIFACT_MANIFEST.txt'
cust_manifest.write_text('\\n'.join(f'{f.name}  SHA256 {sha256(f)}' for f in custodian_files)+'\\n',encoding='utf-8')
cust_zip=out/'sentinel4a-custodian-results.zip'
with zipfile.ZipFile(cust_zip,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for f in custodian_files:z.write(f,f.name)
    z.write(cust_manifest,cust_manifest.name)

receipt={
    'blind_zip':blind_zip.name,'blind_zip_sha256':sha256(blind_zip),
    'custodian_zip':cust_zip.name,'custodian_zip_sha256':sha256(cust_zip),
    'blind_records':len(blind_records),
    'separation_check':'PASS'
}
(out/f'{PREFIX}_ARTIFACT_SEPARATION_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
