#!/usr/bin/env python3
"""EBB-AI-SENTINEL-3C production-compatible RC2 vs RC2.1 live certification runner.

Full mode executes 96 primary records plus 51 RC2.1 high-risk repeats = 147 total.
The blind review JSON intentionally omits version, trial, phase, run_index, endpoint,
model, execution_route, and raw response. Hidden metadata is kept only in custodian files.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,random,time,urllib.request,uuid
from pathlib import Path

DEFAULT_ENDPOINT='https://ucp-backend-4dig.onrender.com/api/claude-proxy'
BASELINE_VERSION='baseline_rc2'
CANDIDATE_VERSION='candidate_rc2_1'
HIGH_RISK={'P01-A','P01-B','P02-B','P03-A','P03-B','P04-B','P06-A','P06-B','P12-B'}
PREFIX='EBB-AI-SENTINEL-3C'

def parse_args():
    here=Path(__file__).resolve().parent
    p=argparse.ArgumentParser()
    p.add_argument('--captured',default=str(here.parent/'01_Captured_Requests'/f'{PREFIX}_CAPTURED_REQUESTS.jsonl'))
    p.add_argument('--endpoint',default=DEFAULT_ENDPOINT)
    p.add_argument('--output-dir',default=str(here/'live_results'))
    p.add_argument('--mode',choices=['quick','full'],default='full')
    p.add_argument('--seed',type=int,default=20260811)
    p.add_argument('--delay',type=float,default=0.35)
    p.add_argument('--timeout',type=float,default=45.0)
    p.add_argument('--retries',type=int,default=2)
    p.add_argument('--plan-only',action='store_true')
    return p.parse_args()

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def extract_text(data):
    if isinstance(data,dict):
        if isinstance(data.get('content'),list):
            parts=[x.get('text','') for x in data['content'] if isinstance(x,dict) and x.get('type')=='text']
            if any(parts): return '\n\n'.join(parts).strip()
        for k in ('response','reply','text'):
            if isinstance(data.get(k),str) and data[k].strip(): return data[k].strip()
    return ''

def post_json(endpoint,payload,timeout,retries):
    body=json.dumps(payload,ensure_ascii=False).encode('utf-8'); last=None
    for attempt in range(retries+1):
        req=urllib.request.Request(endpoint,data=body,method='POST',headers={'Content-Type':'application/json'})
        started=time.time()
        try:
            with urllib.request.urlopen(req,timeout=timeout) as resp:
                raw=resp.read().decode('utf-8',errors='replace')
                elapsed=round(time.time()-started,3)
                try:data=json.loads(raw)
                except Exception:data={'text':raw}
                return {'ok':True,'status':getattr(resp,'status',200),'elapsed_s':elapsed,'data':data,'raw':raw,'attempts':attempt+1}
        except Exception as exc:
            last={'ok':False,'status':getattr(exc,'code',None),'elapsed_s':round(time.time()-started,3),
                  'error':f'{type(exc).__name__}: {exc}','attempts':attempt+1}
            if attempt<retries: time.sleep(1.5*(attempt+1))
    return last

def blind_code(seed,scenario_id,tutor,version,trial):
    return hashlib.sha256(f'{seed}|{scenario_id}|{tutor}|{version}|{trial}'.encode()).hexdigest()[:12].upper()

def build_plan(rows,mode):
    plan=[(r,1,'primary') for r in rows]
    if mode=='full':
        for r in rows:
            if r['version']==CANDIDATE_VERSION and r['scenario_id'] in HIGH_RISK and r['execution_route']=='backend_request':
                for trial in (2,3,4): plan.append((r,trial,'high_risk_repeat'))
    return plan

def main():
    a=parse_args()
    source=Path(a.captured)
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    run_id=str(uuid.uuid4())
    started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    rows=load_jsonl(source)
    assert len(rows)==96
    assert sum(r['version']==BASELINE_VERSION for r in rows)==48
    assert sum(r['version']==CANDIDATE_VERSION for r in rows)==48

    plan=build_plan(rows,a.mode)
    random.seed(a.seed); random.shuffle(plan)
    plan_rows=[]
    for i,(r,trial,phase) in enumerate(plan,1):
        plan_rows.append({
          'run_index':i,'scenario_id':r['scenario_id'],'tutor':r['tutor'],'version':r['version'],
          'trial':trial,'phase':phase,'execution_route':r['execution_route']
        })
    with (out/f'{PREFIX}_EXECUTION_PLAN.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(plan_rows[0]));w.writeheader();w.writerows(plan_rows)

    summary={
      'run_id':run_id,'started_at':started,'mode':a.mode,
      'captured_requests_sha256':file_sha256(source),
      'primary_records':sum(p[2]=='primary' for p in plan),
      'repeat_records':sum(p[2]=='high_risk_repeat' for p in plan),
      'total_records':len(plan),
      'candidate_repeat_groups':len({(r['scenario_id'],r['tutor']) for r,t,p in plan if p=='high_risk_repeat'}),
      'plan_only':bool(a.plan_only)
    }
    if a.plan_only:
        (out/f'{PREFIX}_PLAN_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary,indent=2)); return

    ping_payload={'model':'claude-sonnet-4-6','max_tokens':20,'system':'Reply with exactly: OK',
                  'messages':[{'role':'user','content':'Connection test.'}]}
    ping=post_json(a.endpoint,ping_payload,a.timeout,a.retries)
    (out/'backend_reachability.json').write_text(json.dumps(ping,indent=2,ensure_ascii=False),encoding='utf-8')
    if not ping.get('ok'):
        print('Backend reachability failed. No certification calls were made.')
        print(ping.get('error'))
        raise SystemExit(2)

    results=[]
    for i,(r,trial,phase) in enumerate(plan,1):
        base={k:r.get(k) for k in [
          'scenario_id','category','case_type','routing','version','tutor','synthetic_user_message',
          'required_candidate_behavior','failure_target','execution_route','payload_sha256'
        ]}
        rec=dict(base)
        rec.update({'trial':trial,'phase':phase,'run_index':i,'endpoint':a.endpoint,'run_id':run_id})
        if r['execution_route']=='local_interruption':
            rec.update({'ok':True,'http_status':'LOCAL','elapsed_s':0,'response_text':r.get('local_result') or '',
                        'raw_response':'','model':'LOCAL_FIXED_PATH','stop_reason':'LOCAL'})
        else:
            got=post_json(a.endpoint,r['payload'],a.timeout,a.retries)
            rec['ok']=bool(got.get('ok'));rec['http_status']=got.get('status');rec['elapsed_s']=got.get('elapsed_s')
            if got.get('ok'):
                data=got.get('data',{})
                rec['response_text']=extract_text(data)
                rec['raw_response']=got.get('raw','')
                rec['model']=data.get('model') if isinstance(data,dict) else None
                rec['stop_reason']=data.get('stop_reason') if isinstance(data,dict) else None
            else:
                rec['response_text']='';rec['raw_response']='';rec['error']=got.get('error')
            time.sleep(a.delay)
        rec['blind_code']=blind_code(a.seed,rec['scenario_id'],rec['tutor'],rec['version'],trial)
        results.append(rec)
        with (out/'LIVE_RESPONSES_CHECKPOINT.jsonl').open('w',encoding='utf-8') as f:
            for x in results:f.write(json.dumps(x,ensure_ascii=False)+'\n')
        print(f"[{i}/{len(plan)}] {'OK' if rec.get('ok') else 'ERR'} {rec['scenario_id']} {rec['tutor']} {rec['version']} trial {trial}")

    with (out/f'{PREFIX}_LIVE_RESPONSES.jsonl').open('w',encoding='utf-8') as f:
        for x in results:f.write(json.dumps(x,ensure_ascii=False)+'\n')
    fields=['blind_code','scenario_id','category','case_type','routing','tutor','version','trial','phase',
            'execution_route','ok','http_status','elapsed_s','model','stop_reason','response_text',
            'required_candidate_behavior','failure_target','error','run_id']
    with (out/f'{PREFIX}_LIVE_RESPONSES.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([{k:x.get(k,'') for k in fields} for x in results])

    blind=[]; key=[]
    for x in results:
        blind.append({
          'blind_code':x['blind_code'],'scenario_id':x['scenario_id'],'category':x['category'],
          'case_type':x['case_type'],'routing':x['routing'],'tutor':x['tutor'],
          'synthetic_user_message':x['synthetic_user_message'],
          'required_candidate_behavior':x['required_candidate_behavior'],
          'failure_target':x['failure_target'],'response_text':x.get('response_text','')
        })
        key.append({
          'blind_code':x['blind_code'],'version':x['version'],'scenario_id':x['scenario_id'],
          'tutor':x['tutor'],'trial':x['trial'],'phase':x['phase'],'run_id':run_id
        })
    random.shuffle(blind)
    (out/f'{PREFIX}_BLIND_REVIEW_INPUT.json').write_text(json.dumps(blind,indent=2,ensure_ascii=False),encoding='utf-8')
    with (out/f'{PREFIX}_BLIND_KEY.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(key[0]));w.writeheader();w.writerows(key)

    summary.update({
      'endpoint':a.endpoint,'errors':sum(not x.get('ok') for x in results),
      'completed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'plan_only':False
    })
    (out/f'{PREFIX}_LIVE_RUN_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
