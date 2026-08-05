#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parent
REPORTS=ROOT/"reports-v0.jsonl"; CASES=ROOT/"cases-v0.jsonl"
EXPECTED_REPORTS="sha256:e0b8f561ba45eafe1d12ce3278c46edcf700356b02f674246ac93ed6e7b41c91"
EXPECTED_CASES="sha256:3e82d4e2348826a034946bd7f00c042ba706f161cf1b01b9bf5f87beded2616f"
def canon(p): return p.read_bytes().replace(b"\r\n",b"\n").replace(b"\r",b"\n")
def digest(p): return "sha256:"+hashlib.sha256(canon(p)).hexdigest()
def rows(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def obj(p): return json.loads(p.read_text(encoding="utf-8"))
def validate(rs,schema,label):
 v=Draft202012Validator(schema)
 for i,r in enumerate(rs,1):
  es=list(v.iter_errors(r))
  if es: raise AssertionError(f"{label} {i}: {es[0].message}")
def provider(node,path="<root>"):
 if not isinstance(node,dict): return
 if "const" in node and "type" not in node: raise AssertionError(f"const without type {path}")
 if node.get("type")=="object":
  if node.get("additionalProperties") is not False: raise AssertionError(f"open object {path}")
  if set(node.get("required",[]))!=set(node.get("properties",{})): raise AssertionError(f"optional field {path}")
 if node.get("type")=="array" and "items" not in node: raise AssertionError(f"array items missing {path}")
 for k,v in node.items():
  if isinstance(v,dict): provider(v,path+"/"+k)
  elif isinstance(v,list):
   for i,x in enumerate(v): provider(x,path+f"/{k}/{i}")
def main():
 rs,cs=rows(REPORTS),rows(CASES)
 validate(rs,obj(ROOT/"report-v0.schema.json"),"report")
 validate(cs,obj(ROOT/"case-v0.schema.json"),"case")
 provider(obj(ROOT/"codex-response-v0.schema.json"))
 assert digest(REPORTS)==EXPECTED_REPORTS,(digest(REPORTS),EXPECTED_REPORTS)
 assert digest(CASES)==EXPECTED_CASES,(digest(CASES),EXPECTED_CASES)
 assert len(rs)==11 and len(cs)==11
 ids={x["fusionId"] for x in rs}; assert ids=={x["caseId"] for x in cs}
 for c in cs: assert EXPECTED_REPORTS in c["sourceHashes"]
 dep=next(c for c in cs if c["caseId"]=="management.d2.dependent-duplicate")
 ind=next(c for c in cs if c["caseId"]=="management.d2.independent-corroboration")
 assert dep["expectedExactConclusion"]=="qualified_uncertain"
 assert ind["expectedExactConclusion"]=="assert_with_evidence"
 assert dep["expectedByCondition"]["naive_independent"]["conclusion"]=="assert_with_evidence"
 assert dep["expectedByCondition"]["raw_declared"]["conclusion"]=="qualified_uncertain"
 print("DSL-D2 dependency fusion contract passed")
 print(f"Reports: {len(rs)}"); print(f"Cases: {len(cs)}")
 print(f"Reports hash: {digest(REPORTS)}"); print(f"Cases hash: {digest(CASES)}")
 return 0
if __name__=="__main__": raise SystemExit(main())
