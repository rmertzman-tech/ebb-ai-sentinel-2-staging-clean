#!/usr/bin/env python3
"""Fail closed unless a SENTINEL-8A live result set exactly satisfies the 147-record contract."""
from pathlib import Path
import argparse,csv,json,sys,hashlib
from collections import Counter,defaultdict

PREFIX='EBB-AI-SENTINEL-8A'
BASE='baseline_rc2_5'
CAND='candidate_rc2_6'
HIGH_RISK={'P01-A','P01-B','P02-B','P03-A','P03-B','P04-B','P06-A','P06-B','P12-B'}
FORBIDDEN_BLIND={'version','trial','phase','run_index','endpoint','model','execution_route','raw_response','run_id'}
EXPECTED_BLIND={'blind_code','scenario_id','category','case_type','routing','tutor','synthetic_user_message','required_candidate_behavior','failure_target','response_text'}

p=argparse.ArgumentParser()
p.add_argument('--results-dir',required=True)
p.add_argument('--out',default=None)
a=p.parse_args()
d=Path(a.results_dir)
report=[]

def check(name,cond,detail=''):
    report.append({'check':name,'status':'PASS' if cond else 'FAIL','detail':detail})
    return cond

def load_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def load_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

live=load_jsonl(d/f'{PREFIX}_LIVE_RESPONSES.jsonl')
blind=json.loads((d/f'{PREFIX}_BLIND_REVIEW_INPUT.json').read_text(encoding='utf-8'))
key=load_csv(d/f'{PREFIX}_BLIND_KEY.csv')
summary=json.loads((d/f'{PREFIX}_LIVE_RUN_SUMMARY.json').read_text(encoding='utf-8'))
plan=load_csv(d/f'{PREFIX}_EXECUTION_PLAN.csv')
reach=json.loads((d/'backend_reachability.json').read_text(encoding='utf-8'))

codes=[x['blind_code'] for x in live]
blind_codes=[x['blind_code'] for x in blind]
key_codes=[x['blind_code'] for x in key]
check('backend_reachable', bool(reach.get('ok')), str(reach.get('status')))
check('summary_zero_errors', summary.get('errors')==0, str(summary.get('errors')))
check('live_147', len(live)==147, str(len(live)))
check('plan_147', len(plan)==147, str(len(plan)))
check('blind_147', len(blind)==147, str(len(blind)))
check('key_147', len(key)==147, str(len(key)))
check('unique_live_codes', len(set(codes))==147, str(len(set(codes))))
check('unique_blind_codes', len(set(blind_codes))==147, str(len(set(blind_codes))))
check('unique_key_codes', len(set(key_codes))==147, str(len(set(key_codes))))
check('code_sets_exact', set(codes)==set(blind_codes)==set(key_codes), '')
check('all_live_ok', all(bool(x.get('ok')) for x in live), str(sum(not bool(x.get('ok')) for x in live)))
check('all_responses_nonempty', all(bool((x.get('response_text') or '').strip()) for x in live), str(sum(not bool((x.get('response_text') or '').strip()) for x in live)))

primary=[x for x in live if str(x.get('trial'))=='1']
repeats=[x for x in live if str(x.get('trial'))!='1']
check('primary_96', len(primary)==96, str(len(primary)))
check('baseline_primary_48', sum(x.get('version')==BASE for x in primary)==48, str(sum(x.get('version')==BASE for x in primary)))
check('candidate_primary_48', sum(x.get('version')==CAND for x in primary)==48, str(sum(x.get('version')==CAND for x in primary)))
check('repeat_51', len(repeats)==51, str(len(repeats)))
check('repeats_candidate_only', all(x.get('version')==CAND for x in repeats), '')
check('repeat_trials_2_3_4_only', set(str(x.get('trial')) for x in repeats)=={'2','3','4'}, str(sorted(set(str(x.get('trial')) for x in repeats))))
check('repeat_phase_exact', all(x.get('phase')=='high_risk_repeat' for x in repeats), '')
check('primary_phase_exact', all(x.get('phase')=='primary' for x in primary), '')

groups=defaultdict(list)
for x in repeats: groups[(x['scenario_id'],x['tutor'])].append(int(x['trial']))
check('repeat_groups_17', len(groups)==17, str(len(groups)))
check('three_repeats_each', all(sorted(v)==[2,3,4] for v in groups.values()), '')
check('repeat_scenarios_high_risk_only', all(k[0] in HIGH_RISK for k in groups), '')
check('no_repeat_local_interruptions', all(x.get('execution_route')=='backend_request' for x in repeats), '')

local=[x for x in live if x.get('execution_route')=='local_interruption']
check('local_interruptions_exactly_2', len(local)==2, str(len(local)))
check('local_interruptions_p06a_navigator_primary', all(
    x.get('scenario_id')=='P06-A' and x.get('tutor')=='Navigator Twin' and str(x.get('trial'))=='1'
    for x in local
), '')

# Blind schema and absence of hidden fields
blind_schema_ok=all(set(x.keys())==EXPECTED_BLIND for x in blind)
check('blind_schema_exact', blind_schema_ok, '')
leaks=[(i+1,sorted(set(x.keys()) & FORBIDDEN_BLIND)) for i,x in enumerate(blind) if set(x.keys()) & FORBIDDEN_BLIND]
check('blind_no_hidden_fields', not leaks, str(leaks[:5]))

# Blind response text and public metadata match live.
live_by={x['blind_code']:x for x in live}
public_fields=['scenario_id','category','case_type','routing','tutor','synthetic_user_message','required_candidate_behavior','failure_target','response_text']
blind_match=all(all(str(x.get(k,''))==str(live_by[x['blind_code']].get(k,'')) for k in public_fields) for x in blind)
check('blind_matches_live_public_fields',blind_match,'')

# Key matches hidden metadata exactly
key_by={x['blind_code']:x for x in key}
hidden_fields=['version','scenario_id','tutor','trial','phase','run_id']
key_match=all(all(str(key_by[c].get(k,''))==str(live_by[c].get(k,'')) for k in hidden_fields) for c in codes)
check('key_matches_live_hidden_fields',key_match,'')

# P09-A candidate primaries must be present for the special release gate.
p09=[x for x in primary if x.get('version')==CAND and x.get('scenario_id')=='P09-A']
check('candidate_p09a_primary_two',len(p09)==2,str(len(p09)))

# Summary contract
check('summary_primary_96',summary.get('primary_records')==96,str(summary.get('primary_records')))
check('summary_repeats_51',summary.get('repeat_records')==51,str(summary.get('repeat_records')))
check('summary_total_147',summary.get('total_records')==147,str(summary.get('total_records')))
check('summary_repeat_groups_17',summary.get('candidate_repeat_groups')==17,str(summary.get('candidate_repeat_groups')))

ok=all(r['status']=='PASS' for r in report)
result={'status':'PASS' if ok else 'FAIL','checks':report}
out=Path(a.out) if a.out else d/f'{PREFIX}_POSTRUN_VALIDATION.json'
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
csv_out=out.with_suffix('.csv')
with csv_out.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['check','status','detail']);w.writeheader();w.writerows(report)
print(json.dumps(result,indent=2))
if not ok: raise SystemExit(2)
