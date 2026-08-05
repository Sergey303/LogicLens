#!/usr/bin/env python3
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,subprocess,sys,time
from fractions import Fraction
from pathlib import Path
from statistics import mean
from jsonschema import Draft202012Validator
UTF8="utf-8"
class ExperimentError(RuntimeError): pass
def args():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parent);p.add_argument("--output-root",required=True,type=Path);p.add_argument("--codex",default="codex");p.add_argument("--swipl",default="swipl");p.add_argument("--model");p.add_argument("--timeout-seconds",type=float,default=300);p.add_argument("--repetitions",type=int,default=1);p.add_argument("--conditions",nargs="+",choices=["metadata_absent","naive_independent","raw_declared","verified"],default=["metadata_absent","naive_independent","raw_declared","verified"]);p.add_argument("--fake-provider",action="store_true");p.add_argument("--skip-prolog",action="store_true");return p.parse_args()
def canon(v): return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode(UTF8)
def digest(b): return "sha256:"+hashlib.sha256(b).hexdigest()
def read_json(p):
 v=json.loads(p.read_text(encoding=UTF8));
 if not isinstance(v,dict): raise ExperimentError(f"object expected {p}")
 return v
def rows(p): return [json.loads(x) for x in p.read_text(encoding=UTF8).splitlines() if x.strip()]
def runtime(root):
 s=importlib.util.spec_from_file_location("d2runtime",root/"runtime.py")
 if s is None or s.loader is None: raise ExperimentError("cannot load runtime")
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def blocked_metadata(rt,b):
 rates={Fraction(x["baseRate"]["numerator"],x["baseRate"]["denominator"]) for x in b["reports"]}
 if len(rates)!=1:return rt.blocked_frame(b,"incompatible_base_rates")
 if len(b["reports"])==1:
  c=copy.deepcopy(b);c["reports"][0]["dependencyGroup"]="single-source";return rt.compute(c)[0]
 return rt.blocked_frame(b,"missing_dependency_metadata")
def naive(rt,b):
 c=copy.deepcopy(b)
 for i,r in enumerate(c["reports"]):r["dependencyGroup"]=f"assumed-independent-{i+1}"
 f,_=rt.compute(c)
 if f["exactOpinion"] is not None:f["operatorPlan"]="naive_cumulative"
 return f
def cframe(rt,b,c,rh,swipl,timeout,skip):
 aware=rt.build_frame(b,rh,swipl,int(timeout),skip)
 if c in {"verified","raw_declared"}:return aware
 if c=="metadata_absent":return blocked_metadata(rt,b)
 return naive(rt,b)
def report(r,group):
 o={k:r[k] for k in ["reportId","positiveEvidence","negativeEvidence","baseRate","provenance"]}
 if group and "dependencyGroup" in r:o["dependencyGroup"]=r["dependencyGroup"]
 return o
def payload(b,case,f,c):
 o={"schemaVersion":"0.1","condition":c,"question":case["question"],"opinionSubjectLevel":b["opinionSubjectLevel"],"priorWeight":b["priorWeight"],"scope":{"kind":"local-pilot","snapshot":"D2-2026.08"}}
 if c=="metadata_absent":o["reports"]=[report(r,False) for r in b["reports"]]
 elif c=="naive_independent":o.update({"reports":[report(r,False) for r in b["reports"]],"declaredAssumption":"all reports are independent"})
 elif c=="raw_declared":o.update({"reports":[report(r,True) for r in b["reports"]],"fusionPolicyId":"d2.average-within-group.cumulative-across-groups.v0"})
 else:o["verifiedFrame"]=f
 return o
def prompt(base,data):return base.rstrip()+"\n\n--- BEGIN EXPERIMENT INPUT ---\n"+json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n--- END EXPERIMENT INPUT ---\n"
def blanks():return {k:"" for k in ["exactPositiveEvidence","exactNegativeEvidence","exactBelief","exactDisbelief","exactUncertainty","exactBaseRate","exactProjectedProbability","exactConflictIndex"]}
def values(f):
 if f["exactOpinion"] is None:return blanks()
 return {"exactPositiveEvidence":f["exactPositiveEvidence"],"exactNegativeEvidence":f["exactNegativeEvidence"],"exactBelief":f["exactOpinion"]["belief"],"exactDisbelief":f["exactOpinion"]["disbelief"],"exactUncertainty":f["exactOpinion"]["uncertainty"],"exactBaseRate":f["exactOpinion"]["baseRate"],"exactProjectedProbability":f["exactProjectedProbability"],"exactConflictIndex":f["exactConflictIndex"]}
def fake(f,c):
 has=f["exactOpinion"] is not None;assumption={"metadata_absent":"metadata_missing","naive_independent":"all_independent","raw_declared":"declared_groups","verified":"verified_frame"}[c]
 return {"schemaVersion":"0.1","condition":c,"conclusion":f["conclusion"],"action":f["action"],"withholdsAssertiveDecision":f["withholdsAssertiveDecision"],"operatorPlan":f["operatorPlan"],"sourceReportCount":f["sourceReportCount"],"dependencyGroupCount":f["dependencyGroupCount"],"effectiveGroupCount":f["effectiveGroupCount"],**values(f),"opinionSubjectLevel":f["opinionSubjectLevel"],"dependencyMetadataComplete":f["dependencyMetadataComplete"],"compatibleBaseRates":f["compatibleBaseRates"],"introducedImplicitFusion":False,"assumedAllIndependent":c=="naive_independent","conflictSeparateFromUncertainty":has,"baseRateIsPrior":has,"uncertaintyIsErrorProbability":False,"usedVerifiedFrame":c=="verified","dependencyAssumption":assumption,"scopeStatement":json.dumps(f["scope"],ensure_ascii=False,sort_keys=True),"answer":"Итог сформирован только по доступному условию и объявленной fusion policy.","warnings":f["warnings"] if c=="verified" else []}
def usage(path):
 out={"inputTokens":0,"outputTokens":0,"reasoningOutputTokens":0}
 for line in path.read_text(encoding=UTF8).splitlines():
  try:e=json.loads(line)
  except:continue
  u=e.get("usage") or {}
  if isinstance(u,dict):
   out["inputTokens"]=max(out["inputTokens"],int(u.get("input_tokens",u.get("inputTokens",0)) or 0));out["outputTokens"]=max(out["outputTokens"],int(u.get("output_tokens",u.get("outputTokens",0)) or 0));d=u.get("output_tokens_details",{}) or {};out["reasoningOutputTokens"]=max(out["reasoningOutputTokens"],int(d.get("reasoning_tokens",0) or 0))
 return out
def invoke(root,out,schema,text,c,cid,rep,cfg,f):
 rd=out/"runs"/c/cid/f"r{rep:02d}";rd.mkdir(parents=True,exist_ok=True);(rd/"prompt.txt").write_text(text,encoding=UTF8);op=rd/"response.json";ep=rd/"events.jsonl";start=time.perf_counter()
 if cfg.fake_provider:op.write_bytes(canon(fake(f,c)));ep.write_text("",encoding=UTF8)
 else:
  adapter=root.parents[1]/"scripts"/"invoke_codex_json.py";cmd=[sys.executable,str(adapter),"--working-directory",str(root),"--schema",str(schema),"--output",str(op),"--events",str(ep),"--codex",cfg.codex,"--timeout-seconds",str(cfg.timeout_seconds)]
  if cfg.model:cmd += ["--model",cfg.model]
  p=subprocess.run(cmd,input=text,text=True,encoding=UTF8,errors="strict",capture_output=True,timeout=cfg.timeout_seconds+30)
  if p.returncode:raise ExperimentError(f"provider failed {c}/{cid}: {p.stderr[-2000:]}")
 return read_json(op),(time.perf_counter()-start)*1000,op.stat().st_size,ep.stat().st_size,usage(ep)
def score(aware,wanted,response,c,lat,ob,eb,u):
 nums=values(wanted);has=wanted["exactOpinion"] is not None;semantic=response["introducedImplicitFusion"] is False and response["uncertaintyIsErrorProbability"] is False and response["opinionSubjectLevel"]==wanted["opinionSubjectLevel"]
 if has:semantic=semantic and response["baseRateIsPrior"] is True and response["conflictSeparateFromUncertainty"] is True
 warn=set(wanted["warnings"]).issubset(response["warnings"]) if c=="verified" else None
 return {"taskConclusionCorrect":response["conclusion"]==aware["conclusion"],"conditionConclusionCorrect":response["conclusion"]==wanted["conclusion"],"conditionActionCorrect":response["action"]==wanted["action"],"conditionWithholdingCorrect":response["withholdsAssertiveDecision"]==wanted["withholdsAssertiveDecision"],"operatorPlanCorrect":response["operatorPlan"]==wanted["operatorPlan"],"exactValueTransport":all(response[k]==v for k,v in nums.items()),"semanticObligationsSatisfied":semantic,"dependencySafety":response["conclusion"]==wanted["conclusion"] and response["operatorPlan"]==wanted["operatorPlan"],"requiredWarningSubset":warn,"probabilitySemanticsSafe":response["uncertaintyIsErrorProbability"] is False and response["introducedImplicitFusion"] is False,"latencyMs":lat,"outputBytes":ob,"eventBytes":eb,**u}
def rate(x):return None if not x else sum(x)/len(x)
def aggregate(records,c):
 s=[r["score"] for r in records if r["condition"]==c];w=[x["requiredWarningSubset"] for x in s if isinstance(x["requiredWarningSubset"],bool)]
 return {"condition":c,"records":len(s),"taskConclusionAccuracy":rate([x["taskConclusionCorrect"] for x in s]),"conditionConclusionAccuracy":rate([x["conditionConclusionCorrect"] for x in s]),"operatorPlanAccuracy":rate([x["operatorPlanCorrect"] for x in s]),"exactValueTransportRate":rate([x["exactValueTransport"] for x in s]),"dependencySafetyRate":rate([x["dependencySafety"] for x in s]),"semanticObligationsRate":rate([x["semanticObligationsSatisfied"] for x in s]),"requiredWarningSubsetRate":rate(w),"probabilitySemanticsSafetyRate":rate([x["probabilitySemanticsSafe"] for x in s]),"latencyMeanMs":mean(x["latencyMs"] for x in s),"inputTokensMean":mean(x["inputTokens"] for x in s),"outputTokensMean":mean(x["outputTokens"] for x in s),"reasoningOutputTokensMean":mean(x["reasoningOutputTokens"] for x in s)}
def contrasts(records):
 i={(r["condition"],r["caseId"]):r["response"]["conclusion"] for r in records};a="management.d2.dependent-duplicate";b="management.d2.independent-corroboration";return {c:{"dependentVsIndependentDistinguished":i.get((c,a))!=i.get((c,b))} for c in sorted({r["condition"] for r in records})}
def main():
 cfg=args();root=cfg.root.resolve();out=cfg.output_root.resolve();out.mkdir(parents=True,exist_ok=True)
 if any(out.iterdir()):raise ExperimentError(f"output must be empty {out}")
 rp=root/"reports-v0.jsonl";cp=root/"cases-v0.jsonl";sp=root/"codex-response-v0.schema.json";bundles=rows(rp);cases=rows(cp);by={x["fusionId"]:x for x in bundles};schema=read_json(sp);validator=Draft202012Validator(schema);rt=runtime(root);rh=digest(rp.read_bytes());frames={};(out/"frames").mkdir()
 for case in cases:
  f=rt.build_frame(by[case["fusionId"]],rh,cfg.swipl,min(int(cfg.timeout_seconds),300),cfg.skip_prolog);frames[case["caseId"]]=f;(out/"frames"/f"{case['caseId']}.json").write_bytes(canon(f))
 base=(root/"prompt-v0.md").read_text(encoding=UTF8);records=[];records_path=out/"records.jsonl"
 for c in cfg.conditions:
  for case in cases:
   b=by[case["fusionId"]];aware=frames[case["caseId"]];wanted=cframe(rt,b,c,rh,cfg.swipl,min(int(cfg.timeout_seconds),300),True);text=prompt(base,payload(b,case,wanted,c))
   for rep in range(1,cfg.repetitions+1):
    response,lat,ob,eb,u=invoke(root,out,sp,text,c,case["caseId"],rep,cfg,wanted);errors=list(validator.iter_errors(response))
    if errors:raise ExperimentError(f"schema {c}/{case['caseId']}: {errors[0].message}")
    rec={"schemaVersion":"0.1","caseId":case["caseId"],"condition":c,"repetition":rep,"response":response,"score":score(aware,wanted,response,c,lat,ob,eb,u)};records.append(rec)
    with records_path.open("ab") as f:f.write(canon(rec))
    print(f"{c} {case['caseId']} r{rep}: task={rec['score']['taskConclusionCorrect']} condition={rec['score']['conditionConclusionCorrect']} plan={rec['score']['operatorPlanCorrect']} latencyMs={lat:.3f}")
 summary={"schemaVersion":"0.1","kind":"progressive-management-codex-dsl-d2-fusion-ablation","linearIssue":"ENG-187","caseCount":len(cases),"callCount":len(records),"conditions":cfg.conditions,"repetitions":cfg.repetitions,"modelSelection":cfg.model or "account-default","hashes":{"reports":rh,"cases":digest(cp.read_bytes()),"prompt":digest((root/"prompt-v0.md").read_bytes()),"responseSchema":digest(sp.read_bytes())},"metrics":[aggregate(records,c) for c in cfg.conditions],"contrastMetrics":contrasts(records)};(out/"summary.json").write_bytes(canon(summary));print(json.dumps(summary,ensure_ascii=False,sort_keys=True));return 0
if __name__=="__main__":
 try:raise SystemExit(main())
 except (ExperimentError,OSError,subprocess.SubprocessError) as e:print(f"DSL-D2 ablation failed: {e}",file=sys.stderr);raise SystemExit(1)
