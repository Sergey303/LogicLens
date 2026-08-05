#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict, deque
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator, FormatChecker

PACKET=["TASK.md","REQUIRED_READING.md","INPUT_MANIFEST.json","ALLOWED_PATHS.txt","FORBIDDEN_PATHS.txt","ACCEPTANCE.yaml","HANDOFF_SCHEMA.json"]
CLASSES={"artifact","scientific","independence","adversarial","reproducibility"}
ROB={f"ROB-00{i}" for i in range(1,6)}
SPLITS={"WP-201":{"WP-201A","WP-201B"},"WP-203":{"WP-203A","WP-203B","WP-203C"},"WP-301":{"WP-301H","WP-301R"}}
BANNED=["approved predecessor artifacts","issue acceptance pass","issue stop/pivot","required non-sealed contracts and linear package"]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def err(fs,code,msg,**details): fs.append({"severity":"ERROR","code":code,"message":msg,"details":details})
def flat(v):
    if isinstance(v,str): return v.lower()
    if isinstance(v,list): return " ".join(flat(x) for x in v)
    if isinstance(v,dict): return " ".join(flat(x) for x in v.values())
    return ""
def topo(nodes):
    indeg={n:0 for n in nodes}; succ=defaultdict(list)
    for n,s in nodes.items():
        for d in s["dependencies"]:
            if d in nodes: indeg[n]+=1; succ[d].append(n)
    q=deque(sorted(n for n,v in indeg.items() if v==0)); out=[]
    while q:
        n=q.popleft(); out.append(n)
        for x in sorted(succ[n]):
            indeg[x]-=1
            if indeg[x]==0:q.append(x)
    return out,succ
def reaching(nodes,terminal):
    succ=defaultdict(list)
    for n,s in nodes.items():
        for d in s["dependencies"]: succ[d].append(n)
    ok=set()
    for start in nodes:
        stack=[start]; seen=set()
        while stack:
            x=stack.pop()
            if x==terminal: ok.add(start); break
            if x in seen: continue
            seen.add(x); stack.extend(succ[x])
    return ok
def longest(nodes,order,terminal):
    dist={n:1 for n in nodes}; prev={n:None for n in nodes}
    for n in order:
        for d in nodes[n]["dependencies"]:
            if dist[d]+1>dist[n]: dist[n]=dist[d]+1; prev[n]=d
    path=[]; cur=terminal
    while cur is not None: path.append(cur); cur=prev[cur]
    return list(reversed(path)),dist[terminal]

def merge_dict(dst, src, source, findings):
    for key,value in src.items():
        if key=="nodes":
            dst.setdefault("nodes",{})
            for nid,spec in value.items():
                if nid in dst["nodes"]: err(findings,"DUPLICATE_INCLUDED_NODE",nid,source=str(source))
                dst["nodes"][nid]=spec
        elif key in dst:
            err(findings,"DUPLICATE_INCLUDED_KEY",key,source=str(source))
        else:
            dst[key]=value

def load_work_packages(path, findings):
    manifest=yaml.safe_load(path.read_text(encoding="utf-8"))
    if manifest.get("format")!="split-dag-manifest": return manifest,[]
    includes=manifest.get("includes",[])
    if not includes or includes[0]!="work-packages/program.yaml": err(findings,"INCLUDE_MANIFEST","program registry must be first",actual=includes)
    phase_order={f"W{i}":i for i in range(6)}; seen=[]
    for rel in includes[1:]:
        m=re.fullmatch(r"work-packages/fragments/(W[0-5])-\d{2}\.yaml",rel)
        if not m: err(findings,"INCLUDE_MANIFEST","invalid fragment path",path=rel); continue
        seen.append(phase_order[m.group(1)])
    if seen!=sorted(seen): err(findings,"INCLUDE_MANIFEST","phase fragments are out of order",actual=includes)
    data={"schema_version":manifest.get("schema_version")}; included=[]
    for rel in includes:
        f=path.parent/rel
        if not f.exists(): err(findings,"INCLUDE_MISSING",rel); continue
        included.append(f); part=yaml.safe_load(f.read_text(encoding="utf-8")) or {}; merge_dict(data,part,f,findings)
    return data,included

def main():
    ap=argparse.ArgumentParser(); here=Path(__file__).resolve().parent.parent
    ap.add_argument("--work-packages",type=Path,default=here/"WORK_PACKAGES.yaml")
    ap.add_argument("--schema",type=Path,default=here/"schemas/work-package.schema.json")
    ap.add_argument("--handoff-schema",type=Path,default=here/"schemas/work-package-handoff.schema.json")
    ap.add_argument("--linear-snapshot",type=Path,default=here/"validation/linear-relations-snapshot.json")
    ap.add_argument("--critical-path",type=Path,default=here/"CRITICAL_PATH.md")
    ap.add_argument("--report",type=Path,default=here/"validation/validation-report.json")
    ap.add_argument("--as-of",required=True)
    a=ap.parse_args(); fs=[]
    for f in [a.work_packages,a.schema,a.handoff_schema,a.linear_snapshot,a.critical_path]:
        if not f.exists():err(fs,"FILE_MISSING",str(f))
    if fs:
        report={"status":"FAIL","as_of":a.as_of,"findings":fs}; a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2)); return 1
    data,included_files=load_work_packages(a.work_packages,fs)
    sch=json.loads(a.schema.read_text(encoding="utf-8")); hs=json.loads(a.handoff_schema.read_text(encoding="utf-8")); snap=json.loads(a.linear_snapshot.read_text(encoding="utf-8")); doc=a.critical_path.read_text(encoding="utf-8")
    for e in Draft202012Validator(sch,format_checker=FormatChecker()).iter_errors(data): err(fs,"SCHEMA",e.message,path="/".join(map(str,e.path)))
    try: Draft202012Validator.check_schema(hs)
    except Exception as e:err(fs,"HANDOFF_SCHEMA",str(e))
    nodes=data.get("nodes",{}); roles=set(data.get("role_registry",[])); graph=data.get("graph",{})
    if len(nodes)!=40:err(fs,"NODE_COUNT","expected 40",actual=len(nodes))
    issues=[s["linear_issue"] for s in nodes.values()]
    if len(set(issues))!=len(issues):err(fs,"DUPLICATE_ISSUE","issues must be unique")
    unknown=sorted({d for s in nodes.values() for d in s["dependencies"] if d not in nodes})
    if unknown:err(fs,"UNKNOWN_DEP",str(unknown))
    roots={n for n,s in nodes.items() if not s["dependencies"]}
    if roots!=set(graph.get("roots",[])):err(fs,"ROOTS","declared roots differ",actual=sorted(roots))
    for g in graph.get("gates",[]):
        if g not in nodes or nodes[g]["kind"]!="gate":err(fs,"GATE_KIND",g)
    for n,s in nodes.items():
        if n.startswith("GATE-")!=(s["kind"]=="gate"):err(fs,"KIND_ID",n)
    order,_=topo(nodes)
    if len(order)!=len(nodes):err(fs,"CYCLE","topological sort incomplete",count=len(order))
    edge_count=sum(len(s["dependencies"]) for s in nodes.values())
    if edge_count!=68:err(fs,"EDGE_COUNT","expected 68",actual=edge_count)
    if graph.get("submission_terminal")!="WP-406" or nodes.get("WP-406",{}).get("dependencies")!=["GATE-401"]: err(fs,"SUBMISSION_TERMINAL","GATE-401 must lead to WP-406")
    if graph.get("lifecycle_terminal")!="WP-504":err(fs,"LIFECYCLE_TERMINAL","must be WP-504")
    reach=reaching(nodes,"WP-504")
    if len(reach)!=len(nodes):err(fs,"UNREACHABLE","nodes do not reach WP-504",missing=sorted(set(nodes)-reach))
    issue_to_node={s["linear_issue"]:n for n,s in nodes.items()}
    if set(snap["issues"])!=set(issue_to_node):err(fs,"LINEAR_SET","snapshot issue set differs")
    for issue,e in snap["issues"].items():
        if issue not in issue_to_node:continue
        n=issue_to_node[issue]; s=nodes[n]; deps=[issue_to_node[x] for x in e["direct_blocked_by"] if x in issue_to_node]
        if s["dependencies"]!=deps:err(fs,"LINEAR_DEP_DRIFT",n,yaml=s["dependencies"],snapshot=deps)
        for k,ek in [("producer","producer_role"),("independent_reviewer","reviewer_role"),("gatekeeper","gatekeeper_role")]:
            if s["roles"][k]!=e[ek]:err(fs,"LINEAR_ROLE_DRIFT",n,field=k)
        dh=hashlib.sha256(json.dumps(s["deliverables"],ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
        if dh!=e["deliverables_sha256"]:err(fs,"LINEAR_DELIVERABLE_DRIFT",n,actual=dh,expected=e["deliverables_sha256"])
    for n,s in nodes.items():
        rr=s["roles"]
        if any(rr[k] not in roles for k in ["producer","independent_reviewer","gatekeeper"]):err(fs,"UNKNOWN_ROLE",n)
        if len({rr["producer"],rr["independent_reviewer"],rr["gatekeeper"]})<3:err(fs,"ROLE_COLLISION",n)
        if not all(rr[k] for k in ["identity_record_required","session_separation_required","conflict_declaration_required"]):err(fs,"IDENTITY",n)
        names=[Path(x).name for x in s["context_packet"]["files"]]
        if names!=PACKET:err(fs,"PACKET",n,actual=names)
        if set(s["acceptance"]["checks"])!=CLASSES:err(fs,"CHECK_CLASSES",n)
        if not s["acceptance"]["commands"] or not s["deliverables"] or len(s["actions"])<2:err(fs,"NOT_EXECUTABLE",n)
        txt=flat({k:s[k] for k in ["required_context","allowed_paths","forbidden_context","actions","deliverables","acceptance","stop_or_pivot"]})
        for b in BANNED:
            if b in txt:err(fs,"PLACEHOLDER",n,phrase=b)
        if s["handoff"]["schema"]!="EpistemicCompilerLab/research-execution/schemas/work-package-handoff.schema.json":err(fs,"HANDOFF_REF",n)
        if not s["claim_or_threat_links"]:err(fs,"NO_LINK",n)
    for n,ids in SPLITS.items():
        got={u["id"] for u in nodes[n].get("execution_units",[])}
        if got!=ids:err(fs,"SPLIT",n,expected=sorted(ids),actual=sorted(got))
        for u in nodes[n].get("execution_units",[]):
            if u["producer"]==u["reviewer"]:err(fs,"UNIT_ROLE_COLLISION",u["id"])
    if graph.get("required_blind_sequence")!=["WP-302","WP-303","WP-305","WP-306","GATE-301"]:err(fs,"W3_SEQUENCE","wrong")
    if set(nodes["WP-306"]["dependencies"])!={"WP-303","WP-305"}:err(fs,"UNBLIND_DEPS","WP-306")
    if "WP-303" in nodes["WP-305"]["dependencies"] or "WP-305" in nodes["WP-303"]["dependencies"]:err(fs,"BLIND_SERIAL","runs must be parallel")
    if len({nodes[x]["roles"]["producer"] for x in ["WP-303","WP-305","WP-306"]})!=3:err(fs,"W3_ROLES","operators/analyst collide")
    for x in ["WP-302","WP-303","WP-305"]:
        if "embargo" not in nodes[x]:err(fs,"EMBARGO",x)
    opts=set(data.get("optional_robustness_work",{}))
    if opts!=ROB:err(fs,"OPTIONAL_SET","wrong",actual=sorted(opts))
    docrob=set(re.findall(r"`(ROB-\d{3})`",doc))
    if not ROB.issubset(docrob):err(fs,"DOC_OPTIONAL","missing",actual=sorted(docrob))
    for token in ["WP-406","WP-504","WP-305","WP-306","40 mandatory nodes","68 direct dependency edges","24 nodes / 23 edges","Only W0"]:
        if token not in doc:err(fs,"DOC_DRIFT",token)
    required_bases={"WP-002":{"CLAIM_EVIDENCE_MATRIX.yaml","ABSTRACT_CONTRACT.md","PROHIBITED_CLAIMS.md"},"WP-003":{"RELATED_WORK_MATRIX.csv","NOVELTY_BOUNDARY.md","NEAREST_PRIOR_WORK.md"},"WP-406":{"SUBMISSION_RECEIPT.json","OPENREVIEW_RECORD.md","UPLOADED_HASH_AUDIT.json"}}
    for n,req in required_bases.items():
        got={Path(x).name for x in nodes[n]["deliverables"]}
        if not req.issubset(got):err(fs,"DELIVERABLES",n,missing=sorted(req-got))
    path=[]; ln=0
    if len(order)==len(nodes):
        path,ln=longest(nodes,order,"WP-504")
        if ln!=24:err(fs,"LONGEST","expected 24",actual=ln,path=path)
    errors=[x for x in fs if x["severity"]=="ERROR"]
    report={"schema_version":"1.0.0","status":"FAIL" if errors else "PASS","as_of":a.as_of,"inputs":{"work_packages":{"path":"EpistemicCompilerLab/research-execution/WORK_PACKAGES.yaml","sha256":sha(a.work_packages)},"schema":{"path":"EpistemicCompilerLab/research-execution/schemas/work-package.schema.json","sha256":sha(a.schema)},"handoff_schema":{"path":"EpistemicCompilerLab/research-execution/schemas/work-package-handoff.schema.json","sha256":sha(a.handoff_schema)},"linear_snapshot":{"path":"EpistemicCompilerLab/research-execution/validation/linear-relations-snapshot.json","sha256":sha(a.linear_snapshot)},"critical_path":{"path":"EpistemicCompilerLab/research-execution/CRITICAL_PATH.md","sha256":sha(a.critical_path)},"validator":{"path":"EpistemicCompilerLab/research-execution/scripts/validate_work_packages.py","sha256":sha(Path(__file__).resolve())},"included_files":[{"path":"EpistemicCompilerLab/research-execution/"+str(f.relative_to(a.work_packages.parent)).replace("\\","/"),"sha256":sha(f)} for f in included_files],"assembled_canonical_sha256":hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()},"summary":{"mandatory_nodes":len(nodes),"direct_dependency_edges":edge_count,"roots":sorted(roots),"topological_nodes":len(order),"cycles":0 if len(order)==len(nodes) else 1,"unknown_dependencies":len(unknown),"linear_issues":len(issue_to_node),"optional_robustness_packages":len(opts),"submission_terminal":graph.get("submission_terminal"),"lifecycle_terminal":graph.get("lifecycle_terminal"),"longest_chain_nodes":ln,"longest_chain_edges":max(0,ln-1),"longest_chain":path,"blind_sequence":graph.get("required_blind_sequence")},"checks":{"json_schema":"PASS" if not any(x["code"]=="SCHEMA" for x in errors) else "FAIL","linear_snapshot_alignment":"PASS" if not any(x["code"].startswith("LINEAR_") for x in errors) else "FAIL","acyclicity":"PASS" if len(order)==len(nodes) else "FAIL","roles_and_identity":"PASS" if not any(x["code"] in {"UNKNOWN_ROLE","ROLE_COLLISION","IDENTITY"} for x in errors) else "FAIL","context_packet_executability":"PASS" if not any(x["code"] in {"PACKET","PLACEHOLDER","NOT_EXECUTABLE"} for x in errors) else "FAIL","deliverable_completeness":"PASS" if not any(x["code"] in {"DELIVERABLES","LINEAR_DELIVERABLE_DRIFT"} for x in errors) else "FAIL","composite_splits":"PASS" if not any(x["code"] in {"SPLIT","UNIT_ROLE_COLLISION"} for x in errors) else "FAIL","blind_w3":"PASS" if not any(x["code"] in {"W3_SEQUENCE","UNBLIND_DEPS","BLIND_SERIAL","W3_ROLES","EMBARGO"} for x in errors) else "FAIL","actual_submission_and_w5":"PASS" if not any(x["code"] in {"SUBMISSION_TERMINAL","LIFECYCLE_TERMINAL","UNREACHABLE"} for x in errors) else "FAIL","optional_document_consistency":"PASS" if not any(x["code"] in {"OPTIONAL_SET","DOC_OPTIONAL","DOC_DRIFT"} for x in errors) else "FAIL"},"findings":fs}
    a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if report["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
