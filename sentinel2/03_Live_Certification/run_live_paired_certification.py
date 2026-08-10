#!/usr/bin/env python3
"""EBB-AI-SENTINEL-2 live paired certification runner.

Runs the frozen RC1/RC2 request payloads against the configured production-compatible
Claude proxy. It does not alter prompts, app state, or payloads. It records raw outputs,
creates a blinded review set, and repeats selected high-risk RC2 cases.

Requires ordinary outbound HTTPS access. Uses only Python standard library.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, random, time, urllib.error, urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "https://ucp-backend-4dig.onrender.com/api/claude-proxy"
HIGH_RISK = {
    "P01-A", # genuinely generative - do not invent harm
    "P01-B", # apparent success masking burden
    "P02-B", # constrained staying
    "P03-A", # ordinary phenomenological reopening
    "P03-B", # safety protocol rejected
    "P04-B", # depletion + request to intensify
    "P06-A", # immediate danger (Navigator is local interrupt)
    "P06-B", # safety idiom false positive
    "P12-B", # safety action then clarification
}


def parse_args():
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--captured", default=str(here / "EBB-AI-SENTINEL-2_CAPTURED_REQUESTS.jsonl"))
    p.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    p.add_argument("--output-dir", default=str(here / "live_results"))
    p.add_argument("--mode", choices=["quick", "full"], default="full",
                   help="quick=one primary run; full=primary run plus 3 extra RC2 trials for high-risk backend cases")
    p.add_argument("--seed", type=int, default=20260807)
    p.add_argument("--delay", type=float, default=0.35)
    p.add_argument("--timeout", type=float, default=45.0)
    p.add_argument("--retries", type=int, default=2)
    return p.parse_args()


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def extract_text(data):
    if isinstance(data, dict):
        if isinstance(data.get("content"), list):
            parts = [x.get("text", "") for x in data["content"] if isinstance(x, dict) and x.get("type") == "text"]
            if any(parts): return "\n\n".join(parts).strip()
        for key in ("response", "reply", "text"):
            if isinstance(data.get(key), str) and data[key].strip(): return data[key].strip()
    return ""


def post_json(endpoint, payload, timeout, retries):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(endpoint, data=body, method="POST", headers={"Content-Type": "application/json"})
        started = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                elapsed = round(time.time() - started, 3)
                try: data = json.loads(raw)
                except Exception: data = {"text": raw}
                return {"ok": True, "status": getattr(resp, "status", 200), "elapsed_s": elapsed,
                        "data": data, "raw": raw, "attempts": attempt + 1}
        except Exception as exc:
            elapsed = round(time.time() - started, 3)
            last = {"ok": False, "status": getattr(exc, "code", None), "elapsed_s": elapsed,
                    "error": f"{type(exc).__name__}: {exc}", "attempts": attempt + 1}
            if attempt < retries: time.sleep(1.5 * (attempt + 1))
    return last


def blind_code(seed, scenario_id, tutor, version, trial):
    s = f"{seed}|{scenario_id}|{tutor}|{version}|{trial}".encode()
    return hashlib.sha256(s).hexdigest()[:12].upper()


def main():
    args = parse_args()
    source = Path(args.captured)
    outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(source)
    random.seed(args.seed)

    # Production-compatible reachability test. This uses the same proxy but no autobiographical data.
    ping_payload = {"model":"claude-sonnet-4-6","max_tokens":20,
                    "system":"Reply with exactly: OK","messages":[{"role":"user","content":"Connection test."}]}
    ping = post_json(args.endpoint, ping_payload, args.timeout, args.retries)
    (outdir / "backend_reachability.json").write_text(json.dumps(ping, indent=2, ensure_ascii=False), encoding="utf-8")
    if not ping.get("ok"):
        print("Backend reachability failed. No certification calls were made.")
        print(ping.get("error"))
        raise SystemExit(2)

    plan = []
    for r in rows:
        plan.append((r, 1, "primary"))
    if args.mode == "full":
        for r in rows:
            if r["version"] == "candidate_rc2" and r["scenario_id"] in HIGH_RISK and r["execution_route"] == "backend_request":
                for trial in (2,3,4): plan.append((r, trial, "high_risk_repeat"))
    random.shuffle(plan)

    results = []
    for i, (r, trial, phase) in enumerate(plan, 1):
        base = {k:r.get(k) for k in ["scenario_id","category","case_type","routing","version","tutor","synthetic_user_message","required_candidate_behavior","failure_target","execution_route","payload_sha256"]}
        rec = dict(base)
        rec.update({"trial": trial, "phase": phase, "run_index": i, "endpoint": args.endpoint})
        if r["execution_route"] == "local_interruption":
            rec.update({"ok": True, "http_status": "LOCAL", "elapsed_s": 0, "response_text": r.get("local_result") or "", "raw_response": "", "model": "LOCAL_FIXED_PATH", "stop_reason": "LOCAL"})
        else:
            got = post_json(args.endpoint, r["payload"], args.timeout, args.retries)
            rec["ok"] = bool(got.get("ok")); rec["http_status"] = got.get("status"); rec["elapsed_s"] = got.get("elapsed_s")
            if got.get("ok"):
                data = got.get("data", {})
                rec["response_text"] = extract_text(data)
                rec["raw_response"] = got.get("raw", "")
                rec["model"] = data.get("model") if isinstance(data, dict) else None
                rec["stop_reason"] = data.get("stop_reason") if isinstance(data, dict) else None
            else:
                rec["response_text"] = ""; rec["raw_response"] = ""; rec["error"] = got.get("error")
            time.sleep(args.delay)
        rec["blind_code"] = blind_code(args.seed, rec["scenario_id"], rec["tutor"], rec["version"], trial)
        results.append(rec)
        status = "OK" if rec.get("ok") else "ERR"
        print(f"[{i}/{len(plan)}] {status} {rec['scenario_id']} {rec['tutor']} {rec['version']} trial {trial}")

        # crash-safe checkpoint
        with (outdir / "LIVE_RESPONSES_CHECKPOINT.jsonl").open("w", encoding="utf-8") as f:
            for x in results: f.write(json.dumps(x, ensure_ascii=False)+"\n")

    with (outdir / "EBB-AI-SENTINEL-2_LIVE_RESPONSES.jsonl").open("w", encoding="utf-8") as f:
        for x in results: f.write(json.dumps(x, ensure_ascii=False)+"\n")

    fields = ["blind_code","scenario_id","category","case_type","routing","tutor","version","trial","phase","execution_route","ok","http_status","elapsed_s","model","stop_reason","response_text","required_candidate_behavior","failure_target","error"]
    with (outdir / "EBB-AI-SENTINEL-2_LIVE_RESPONSES.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows([{k:x.get(k,"") for k in fields} for x in results])

    # Blinded reviewer input excludes version. Key is stored separately.
    blind=[]; key=[]
    for x in results:
        blind.append({
            "blind_code":x["blind_code"],"scenario_id":x["scenario_id"],"category":x["category"],"case_type":x["case_type"],
            "routing":x["routing"],"tutor":x["tutor"],"trial":x["trial"],"phase":x["phase"],
            "synthetic_user_message":x["synthetic_user_message"],"required_candidate_behavior":x["required_candidate_behavior"],
            "failure_target":x["failure_target"],"response_text":x.get("response_text","")
        })
        key.append({"blind_code":x["blind_code"],"version":x["version"],"scenario_id":x["scenario_id"],"tutor":x["tutor"],"trial":x["trial"]})
    random.shuffle(blind)
    (outdir / "EBB-AI-SENTINEL-2_BLIND_REVIEW_INPUT.json").write_text(json.dumps(blind,indent=2,ensure_ascii=False),encoding="utf-8")
    with (outdir / "EBB-AI-SENTINEL-2_BLIND_KEY.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(key[0]));w.writeheader();w.writerows(key)

    summary={"mode":args.mode,"endpoint":args.endpoint,"primary_records":sum(x[2]=="primary" for x in plan),"repeat_records":sum(x[2]=="high_risk_repeat" for x in plan),"total_records":len(results),"errors":sum(not x.get("ok") for x in results),"completed_at":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    (outdir / "EBB-AI-SENTINEL-2_LIVE_RUN_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__ == "__main__": main()
