#!/usr/bin/env python3
"""Run Direct/Scalar/Raw/Verified Codex ablation for DSL-D0."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys, time
from pathlib import Path
from statistics import mean
from typing import Any
from jsonschema import Draft202012Validator

UTF8 = "utf-8"

class ExperimentError(RuntimeError):
    pass

def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--output-root", required=True, type=Path)
    p.add_argument("--codex", default="codex")
    p.add_argument("--swipl", default="swipl")
    p.add_argument("--model")
    p.add_argument("--timeout-seconds", type=float, default=300)
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--conditions", nargs="+",
                   choices=["direct","scalar","raw","verified"],
                   default=["direct","scalar","raw","verified"])
    p.add_argument("--fake-provider", action="store_true")
    p.add_argument("--skip-prolog", action="store_true")
    return p.parse_args()

def canon(v: Any) -> bytes:
    return (json.dumps(v, ensure_ascii=False, sort_keys=True,
                       separators=(",",":"), allow_nan=False)+"\n").encode(UTF8)

def digest(v: bytes) -> str:
    return "sha256:"+hashlib.sha256(v).hexdigest()

def read_json(path: Path) -> dict[str, Any]:
    v=json.loads(path.read_text(encoding=UTF8))
    if not isinstance(v,dict): raise ExperimentError(f"object expected: {path}")
    return v

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows=[]
    for n,line in enumerate(path.read_text(encoding=UTF8).splitlines(),1):
        if not line.strip(): continue
        v=json.loads(line)
        if not isinstance(v,dict): raise ExperimentError(f"object expected: {path}:{n}")
        rows.append(v)
    return rows

def load_runtime(root: Path):
    spec=importlib.util.spec_from_file_location("opinion_d0_runtime",root/"runtime.py")
    if spec is None or spec.loader is None: raise ExperimentError("cannot load runtime")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def blank() -> dict[str,str]:
    return {k:"" for k in ("belief","disbelief","uncertainty","baseRate",
                            "projectedProbability","conflictIndex")}

def numbers(frame: dict[str,Any]) -> dict[str,str]:
    if frame["opinion"] is None: return blank()
    return {**{k:frame["opinion"][k] for k in
               ("belief","disbelief","uncertainty","baseRate")},
            "projectedProbability":frame["projectedProbability"],
            "conflictIndex":frame["conflictIndex"]}

def payload(case: dict[str,Any], frame: dict[str,Any], condition: str) -> dict[str,Any]:
    out={"schemaVersion":"0.1","condition":condition,
         "question":case["question"],"scope":frame["scope"]}
    if condition=="scalar": out["projectedProbability"]=frame["projectedProbability"]
    elif condition=="raw":
        out.update({"opinion":None if frame["opinion"] is None else {
            k:frame["opinion"][k] for k in ("belief","disbelief","uncertainty","baseRate")},
            "conflictIndex":frame["conflictIndex"],"level":frame["level"],
            "aggregationPolicyId":frame["aggregationPolicyId"],
            "dependencyGroups":frame["dependencyGroups"],"provenance":frame["provenance"]})
    elif condition=="verified": out["verifiedFrame"]=frame
    return out

def prompt(base: str, data: dict[str,Any]) -> str:
    return base.rstrip()+"\n\n--- BEGIN EXPERIMENT INPUT ---\n"+json.dumps(
        data,ensure_ascii=False,sort_keys=True,indent=2)+"\n--- END EXPERIMENT INPUT ---\n"

def expected(frame: dict[str,Any], condition: str) -> tuple[str,str,bool]:
    if condition=="direct": return "request_opinion","abstain_and_request_opinion",True
    if condition=="scalar": return "scalar_insufficient","abstain_on_scalar",True
    c=frame["allowedConclusion"]
    return c,frame["action"],c in {"request_opinion","abstain_high_uncertainty","report_conflict"}

def fake(frame: dict[str,Any], condition: str) -> dict[str,Any]:
    vals=blank()
    if condition=="direct":
        c,a,stop="request_opinion","abstain_and_request_opinion",True
        us,ur,uv=False,False,False
        semantics=False; answer="Opinion недоступно; требуется запросить профиль."
        warnings=["missing-private-opinion"]
    elif condition=="scalar":
        vals["projectedProbability"]=frame["projectedProbability"] or ""
        c,a,stop="scalar_insufficient","abstain_on_scalar",True
        us,ur,uv=True,False,False
        semantics=False; answer="Один scalar не раскрывает uncertainty, prior и conflict."
        warnings=["scalar-compression-insufficient"]
    else:
        vals=numbers(frame); c,a,stop=expected(frame,condition)
        us,ur,uv=False,condition=="raw",condition=="verified"
        semantics=frame["opinion"] is not None
        answer=("Профиль относится к proposition answer_correct."
                if frame["level"]=="answer" else "Интерпретация полного opinion.")
        warnings=frame["warnings"] if condition=="verified" else ["raw-opinion-interpreted"]
    return {"schemaVersion":"0.1","condition":condition,"conclusion":c,"action":a,
        "abstain":stop,**vals,"usedScalar":us,"usedRawOpinion":ur,"usedVerifiedFrame":uv,
        "baseRateIsPrior":semantics,"uncertaintyIsErrorProbability":False,
        "conflictSeparateFromUncertainty":semantics,"introducedFusion":False,
        "sameProjectionCanDiffer":semantics,
        "answerLevelProfile":frame["level"]=="answer" and condition in {"raw","verified"},
        "scopeStatement":json.dumps(frame["scope"],ensure_ascii=False,sort_keys=True),
        "answer":answer,"warnings":warnings}

def invoke(root: Path, out: Path, schema: Path, text: str, condition: str,
           case_id: str, rep: int, cfg: argparse.Namespace,
           frame: dict[str,Any]) -> tuple[dict[str,Any],float,int,int]:
    run=out/"runs"/condition/case_id/f"r{rep:02d}"; run.mkdir(parents=True)
    pp,op,ep=run/"prompt.txt",run/"response.json",run/"events.jsonl"
    pp.write_text(text,encoding=UTF8); start=time.perf_counter()
    if cfg.fake_provider:
        response=fake(frame,condition); op.write_bytes(canon(response)); ep.write_text("",encoding=UTF8)
    else:
        adapter=root.parents[1]/"scripts"/"invoke_codex_json.py"
        cmd=[sys.executable,str(adapter),"--working-directory",str(root),"--schema",str(schema),
             "--output",str(op),"--events",str(ep),"--codex",cfg.codex,
             "--timeout-seconds",str(cfg.timeout_seconds)]
        if cfg.model: cmd += ["--model",cfg.model]
        p=subprocess.run(cmd,input=text,text=True,encoding=UTF8,errors="strict",
                         capture_output=True,timeout=cfg.timeout_seconds+30)
        if p.returncode:
            raise ExperimentError(f"provider failed {condition}/{case_id}: {p.stderr[-1500:]}")
        response=read_json(op)
    return response,(time.perf_counter()-start)*1000,op.stat().st_size,ep.stat().st_size

def score(frame: dict[str,Any], condition: str, response: dict[str,Any],
          latency: float, ob: int, eb: int) -> dict[str,Any]:
    cc,ca,cs=expected(frame,condition)
    wanted=blank()
    if condition=="scalar": wanted["projectedProbability"]=frame["projectedProbability"] or ""
    elif condition in {"raw","verified"}: wanted=numbers(frame)
    exact={k:response[k] for k in wanted}==wanted
    if condition in {"raw","verified"} and frame["opinion"] is not None:
        semantic=(response["baseRateIsPrior"] is True and
                  response["uncertaintyIsErrorProbability"] is False and
                  response["conflictSeparateFromUncertainty"] is True and
                  response["introducedFusion"] is False and
                  response["sameProjectionCanDiffer"] is True and
                  response["answerLevelProfile"]==(frame["level"]=="answer"))
    else:
        semantic=response["introducedFusion"] is False and response["answerLevelProfile"] is False
    return {"taskConclusionCorrect":response["conclusion"]==frame["allowedConclusion"],
        "conditionConclusionCorrect":response["conclusion"]==cc,
        "conditionActionCorrect":response["action"]==ca,
        "conditionAbstentionCorrect":response["abstain"]==cs,
        "numberTransportExact":exact,"semanticObligationsSatisfied":semantic,
        "warningFidelityExact":response["warnings"]==frame["warnings"] if condition=="verified" else None,
        "scalarOverclaim":condition=="scalar" and response["conclusion"]!="scalar_insufficient",
        "probabilitySemanticsSafe":response["uncertaintyIsErrorProbability"] is False
                                   and response["introducedFusion"] is False,
        "latencyMs":latency,"outputBytes":ob,"eventBytes":eb}

def rate(v: list[bool]) -> float|None:
    return None if not v else sum(v)/len(v)

def aggregate(records: list[dict[str,Any]], condition: str) -> dict[str,Any]:
    s=[r["score"] for r in records if r["condition"]==condition]
    warnings=[x["warningFidelityExact"] for x in s if isinstance(x["warningFidelityExact"],bool)]
    return {"condition":condition,"records":len(s),
        "taskConclusionAccuracy":rate([x["taskConclusionCorrect"] for x in s]),
        "conditionConclusionAccuracy":rate([x["conditionConclusionCorrect"] for x in s]),
        "conditionActionAccuracy":rate([x["conditionActionCorrect"] for x in s]),
        "conditionAbstentionAccuracy":rate([x["conditionAbstentionCorrect"] for x in s]),
        "numberTransportExactRate":rate([x["numberTransportExact"] for x in s]),
        "semanticObligationsRate":rate([x["semanticObligationsSatisfied"] for x in s]),
        "warningFidelityExactRate":rate(warnings),
        "probabilitySemanticsSafetyRate":rate([x["probabilitySemanticsSafe"] for x in s]),
        "scalarOverclaimRate":rate([x["scalarOverclaim"] for x in s]) if condition=="scalar" else None,
        "latencyMeanMs":mean(x["latencyMs"] for x in s),
        "outputBytesMean":mean(x["outputBytes"] for x in s),
        "eventBytesMean":mean(x["eventBytes"] for x in s)}

def contrasts(records: list[dict[str,Any]]) -> dict[str,Any]:
    idx={(r["condition"],r["caseId"]):r["response"]["conclusion"] for r in records}
    pairs={"equalProjection":("management.d0.evidence-dominant-same-p",
                              "management.d0.prior-dominant-same-p"),
           "baseRate":("management.d0.low-base-rate","management.d0.high-base-rate"),
           "conflict":("management.d0.low-conflict-same-p",
                       "management.d0.high-conflict-same-p")}
    out={}
    for cond in sorted({r["condition"] for r in records}):
        out[cond]={name+"Distinguished":idx.get((cond,a))!=idx.get((cond,b))
                   for name,(a,b) in pairs.items()}
    return out

def main() -> int:
    cfg=args()
    if not 1<=cfg.repetitions<=20: raise ExperimentError("repetitions must be in [1,20]")
    root,out=cfg.root.resolve(),cfg.output_root.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ExperimentError(f"output root must be absent or empty: {out}")
    out.mkdir(parents=True,exist_ok=True)
    cp,op,pp,sp=(root/"cases-v0.jsonl",root/"opinions-v0.jsonl",
                 root/"prompt-v0.md",root/"codex-response-v0.schema.json")
    cases,opinions=read_jsonl(cp),read_jsonl(op)
    base=pp.read_text(encoding=UTF8); schema=read_json(sp)
    validator=Draft202012Validator(schema); runtime=load_runtime(root)
    oh=digest(op.read_bytes()); by={x["opinionId"]:x for x in opinions}
    frames={}; (out/"frames").mkdir()
    for case in cases:
        frame=runtime.build_frame(by[case["opinionId"]],opinions_hash=oh,swipl=cfg.swipl,
                                  timeout_seconds=min(int(cfg.timeout_seconds),300),
                                  skip_prolog=cfg.skip_prolog)
        frames[case["caseId"]]=frame
        (out/"frames"/f"{case['caseId']}.json").write_bytes(canon(frame))
    records=[]; rp=out/"records.jsonl"
    for cond in cfg.conditions:
        for case in cases:
            frame=frames[case["caseId"]]; text=prompt(base,payload(case,frame,cond))
            for rep in range(1,cfg.repetitions+1):
                response,lat,ob,eb=invoke(root,out,sp,text,cond,case["caseId"],rep,cfg,frame)
                errors=sorted(validator.iter_errors(response),key=lambda e:list(e.path))
                if errors: raise ExperimentError(f"response schema failure {cond}/{case['caseId']}: {errors[0].message}")
                rec={"schemaVersion":"0.1","caseId":case["caseId"],"condition":cond,
                     "repetition":rep,"question":case["question"],"frameHash":digest(canon(frame)),
                     "response":response,"score":score(frame,cond,response,lat,ob,eb)}
                records.append(rec)
                with rp.open("ab") as f: f.write(canon(rec))
                print(f"{cond} {case['caseId']} r{rep}: "
                      f"task={rec['score']['taskConclusionCorrect']} "
                      f"condition={rec['score']['conditionConclusionCorrect']} "
                      f"numbers={rec['score']['numberTransportExact']} "
                      f"semantics={rec['score']['semanticObligationsSatisfied']} latencyMs={lat:.3f}")
    summary={"schemaVersion":"0.1","kind":"progressive-management-codex-dsl-d0-ablation",
        "caseCount":len(cases),"callCount":len(records),"conditions":cfg.conditions,
        "repetitions":cfg.repetitions,"modelSelection":cfg.model or "account-default",
        "hashes":{"cases":digest(cp.read_bytes()),"opinions":oh,
                  "prompt":digest(pp.read_bytes()),"responseSchema":digest(sp.read_bytes())},
        "metrics":[aggregate(records,c) for c in cfg.conditions],
        "contrastMetrics":contrasts(records)}
    (out/"summary.json").write_bytes(canon(summary))
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True)); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (ExperimentError,OSError,subprocess.SubprocessError) as exc:
        print(f"DSL-D0 Codex ablation failed: {exc}",file=sys.stderr); raise SystemExit(1) from exc
