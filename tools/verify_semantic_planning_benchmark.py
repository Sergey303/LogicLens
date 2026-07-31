#!/usr/bin/env python3
"""Fail-closed verifier for LogicLens semantic-planning benchmark v0."""
from __future__ import annotations

import argparse, hashlib, json, sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

MANIFEST_SCHEMA = "semantic-planning-benchmark-manifest-v0"
CASE_SCHEMA = "semantic-planning-benchmark-case-v0"
PROFILE_SCHEMA = "dataset-profile-v0"
FROZEN_MANIFEST_SHA256 = "24b3e91bf80aca66c1750b8787f5c7cc9abd51492bdec21bbe3f7515477d29ef"

class ValidationError(ValueError): pass

def die(p: str, m: str): raise ValidationError(f"{p}: {m}")
def obj(v: Any, p: str) -> dict:
    if not isinstance(v, dict): die(p, "expected object")
    return v
def arr(v: Any, p: str) -> list:
    if not isinstance(v, list): die(p, "expected array")
    return v
def text(v: Any, p: str, empty=False) -> str:
    if not isinstance(v, str) or (not empty and not v): die(p, "expected non-empty string")
    return v
def integer(v: Any, p: str, minimum=0) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v < minimum: die(p, f"expected integer >= {minimum}")
    return v
def boolean(v: Any, p: str) -> bool:
    if not isinstance(v, bool): die(p, "expected boolean")
    return v
def keys(v: dict, p: str, required: set[str], optional=frozenset()):
    missing, extra = required-set(v), set(v)-required-set(optional)
    if missing: die(p, "missing keys: " + ", ".join(sorted(missing)))
    if extra: die(p, "unknown keys: " + ", ".join(sorted(extra)))
def strings(v: Any, p: str, empty=False) -> list[str]:
    out=[text(x, f"{p}[{i}]") for i,x in enumerate(arr(v,p))]
    if not empty and not out: die(p,"must not be empty")
    if len(out)!=len(set(out)): die(p,"contains duplicates")
    return out
def read_json(path: Path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as e: die(str(path),f"invalid UTF-8/JSON: {e}")
def sha(data: bytes): return hashlib.sha256(data).hexdigest()

@dataclass(frozen=True)
class Summary:
    benchmark_id: str; case_count: int; file_count: int
    def json(self): return {"status":"valid","benchmarkId":self.benchmark_id,"caseCount":self.case_count,"fileCount":self.file_count}

def validate_manifest(root: Path, anchor: str|None):
    mp=root/"manifest.json"
    if not mp.is_file(): die("manifest.json","missing")
    raw=mp.read_bytes()
    if anchor and sha(raw)!=anchor: die("manifest.json",f"frozen trust anchor mismatch: expected {anchor}, found {sha(raw)}")
    m=obj(read_json(mp),"manifest")
    keys(m,"manifest",{"schemaVersion","benchmarkId","status","researchSpecification","caseCount","caseIds","mutationPolicy","files"})
    if m["schemaVersion"]!=MANIFEST_SCHEMA: die("manifest.schemaVersion","unexpected value")
    if m["status"]!="frozen": die("manifest.status","must be frozen")
    if m["mutationPolicy"]!="append-new-version-only": die("manifest.mutationPolicy","unexpected value")
    text(m["benchmarkId"],"manifest.benchmarkId"); text(m["researchSpecification"],"manifest.researchSpecification")
    ids=strings(m["caseIds"],"manifest.caseIds")
    if integer(m["caseCount"],"manifest.caseCount",1)!=len(ids): die("manifest.caseCount","does not match caseIds")
    listed={}; case_paths=[]
    for i,e0 in enumerate(arr(m["files"],"manifest.files")):
        p=f"manifest.files[{i}]"; e=obj(e0,p); keys(e,p,{"path","sha256","bytes"})
        rel=text(e["path"],p+".path"); pp=PurePosixPath(rel)
        if pp.is_absolute() or "\\" in rel or any(x in {"",".",".."} for x in pp.parts): die(p+".path","unsafe path")
        if rel=="manifest.json" or rel in listed: die(p+".path","duplicate/self path")
        h=text(e["sha256"],p+".sha256")
        if len(h)!=64 or any(c not in "0123456789abcdef" for c in h): die(p+".sha256","invalid SHA-256")
        target=root.joinpath(*pp.parts)
        if target.is_symlink(): die(p+".path","symbolic links forbidden")
        if not target.is_file(): die(p+".path","file missing")
        data=target.read_bytes()
        if integer(e["bytes"],p+".bytes")!=len(data): die(p+".bytes","byte count mismatch")
        if sha(data)!=h: die(p+".sha256","content hash mismatch")
        listed[rel]=target
        if rel.startswith("cases/") and rel.endswith(".json"): case_paths.append((rel,target))
    for x in root.rglob("*"):
        if x.is_symlink(): die(x.relative_to(root).as_posix(),"symbolic links forbidden")
    actual={x.relative_to(root).as_posix() for x in root.rglob("*") if x.is_file() and x.name!="manifest.json"}
    if actual!=set(listed): die("manifest.files",f"unlisted files or absent files: {sorted(actual^set(listed))}")
    if len(case_paths)!=m["caseCount"]: die("manifest.caseCount","does not match cases/*.json")
    return m,sorted(case_paths)

def validate_literal(o: dict,p: str):
    keys(o,p,{"kind","lexical","literalKind","language","datatype"}); text(o["lexical"],p+".lexical",True)
    k=text(o["literalKind"],p+".literalKind")
    if k not in {"plain","language","datatype"}: die(p+".literalKind","unsupported")
    lang,dt=o["language"],o["datatype"]
    if lang is not None: text(lang,p+".language")
    if dt is not None: text(dt,p+".datatype")
    if k=="plain" and (lang is not None or dt is not None): die(p,"plain literal requires null language and datatype")
    if k=="language" and (lang is None or dt is not None): die(p,"language literal shape mismatch")
    if k=="datatype" and (lang is not None or dt is None): die(p,"datatype literal shape mismatch")

def validate_case(doc0: Any,path: str)->str:
    d=obj(doc0,path); keys(d,path,{"schemaVersion","caseId","caseKind","researchTargets","task","canonicalFacts","ontologyEvidence","oracleSemanticClaims","oracleDatasetProfile","expectedPresentation"})
    if d["schemaVersion"]!=CASE_SCHEMA: die(path+".schemaVersion","unexpected value")
    cid=text(d["caseId"],path+".caseId")
    if d["caseKind"] not in {"positive","mixed","negative"}: die(path+".caseKind","unsupported")
    strings(d["researchTargets"],path+".researchTargets")
    t=obj(d["task"],path+".task"); keys(t,path+".task",{"language","text","goal","questions","answerKey"}); task_text=text(t["text"],path+".task.text"); text(t["language"],path+".task.language"); text(t["goal"],path+".task.goal")
    qids=[]
    for i,q0 in enumerate(arr(t["questions"],path+".task.questions")):
        p=f"{path}.task.questions[{i}]"; q=obj(q0,p); keys(q,p,{"questionId","text"}); qids.append(text(q["questionId"],p+".questionId")); text(q["text"],p+".text")
    if not qids or len(qids)!=len(set(qids)): die(path+".task.questions","empty/duplicate questionId")
    facts=arr(d["canonicalFacts"],path+".canonicalFacts"); fact_by={}; by_subject={}; predicates=set()
    for i,f0 in enumerate(facts):
        p=f"{path}.canonicalFacts[{i}]"; f=obj(f0,p); keys(f,p,{"factId","subject","predicate","object","origins"})
        fid=text(f["factId"],p+".factId")
        if fid in fact_by: die(p+".factId","duplicate factId")
        s=text(f["subject"],p+".subject"); pr=text(f["predicate"],p+".predicate"); strings(f["origins"],p+".origins")
        o=obj(f["object"],p+".object")
        if o.get("kind")=="literal": validate_literal(o,p+".object")
        elif o.get("kind")=="iri": keys(o,p+".object",{"kind","resourceId"}); text(o["resourceId"],p+".object.resourceId")
        else: die(p+".object.kind","unsupported")
        fact_by[fid]=f; predicates.add(pr); by_subject.setdefault(s,set()).add(pr)
    if not fact_by: die(path+".canonicalFacts","empty")
    labels={}; ontology_ids=set()
    for i,x0 in enumerate(arr(d["ontologyEvidence"],path+".ontologyEvidence")):
        p=f"{path}.ontologyEvidence[{i}]"; x=obj(x0,p); keys(x,p,{"element","labels","definitions"}); el=obj(x["element"],p+".element"); keys(el,p+".element",{"kind","id"})
        if el["kind"]!="predicate": die(p+".element.kind","only predicate supported")
        eid=text(el["id"],p+".element.id")
        if eid in ontology_ids: die(p+".element.id","duplicate")
        ontology_ids.add(eid); labels[eid]=set()
        for j,l0 in enumerate(arr(x["labels"],p+".labels")):
            lp=f"{p}.labels[{j}]"; l=obj(l0,lp); keys(l,lp,{"language","text"}); labels[eid].add(text(l["text"],lp+".text"));
            if l["language"] is not None: text(l["language"],lp+".language")
        for j,z0 in enumerate(arr(x["definitions"],p+".definitions")):
            zp=f"{p}.definitions[{j}]"; z=obj(z0,zp); keys(z,zp,{"language","text"}); text(z["text"],zp+".text");
            if z["language"] is not None: text(z["language"],zp+".language")
    claims=arr(d["oracleSemanticClaims"],path+".oracleSemanticClaims"); claim_by={}
    for i,c0 in enumerate(claims):
        p=f"{path}.oracleSemanticClaims[{i}]"; c=obj(c0,p); keys(c,p,{"claimId","dataElement","facet","role","status","evidence","alternatives"}); clid=text(c["claimId"],p+".claimId")
        if clid in claim_by: die(p+".claimId","duplicate claimId")
        el=obj(c["dataElement"],p+".dataElement"); keys(el,p+".dataElement",{"kind","id"}); eid=text(el["id"],p+".dataElement.id")
        if el["kind"]!="predicate" or eid not in predicates|ontology_ids: die(p+".dataElement","unknown/non-predicate element")
        text(c["facet"],p+".facet"); text(c["role"],p+".role")
        if c["status"] not in {"supported","possible","rejected","unknown"}: die(p+".status","unsupported")
        evs=arr(c["evidence"],p+".evidence")
        if not evs: die(p+".evidence","empty")
        for j,e0 in enumerate(evs):
            ep=f"{p}.evidence[{j}]"; e=obj(e0,ep); kind=text(e.get("kind"),ep+".kind")
            if kind in {"ontology_label","datatype","task_text"}:
                keys(e,ep,{"kind","value"}); v=text(e["value"],ep+".value")
                if kind=="ontology_label" and v not in labels.get(eid,set()): die(ep+".value","not visible ontology label")
                if kind=="datatype" and not any(f["predicate"]==eid and f["object"].get("datatype")==v for f in facts): die(ep+".value","datatype absent")
                if kind=="task_text" and v not in task_text: die(ep+".value","not exact task substring")
            elif kind=="fact_ids":
                keys(e,ep,{"kind","factIds"})
                for r in strings(e["factIds"],ep+".factIds"):
                    if r not in fact_by or fact_by[r]["predicate"]!=eid: die(ep+".factIds",f"unknown/wrong predicate FactId {r}")
            elif kind=="neighboring_predicates":
                keys(e,ep,{"kind","predicateIds"})
                if set(strings(e["predicateIds"],ep+".predicateIds"))-predicates: die(ep+".predicateIds","unknown predicate")
            else: die(ep+".kind","unsupported evidence")
        strings(c["alternatives"],p+".alternatives",True); claim_by[clid]=c
    if not claim_by: die(path+".oracleSemanticClaims","empty")
    for clid,c in claim_by.items():
        for a in c["alternatives"]:
            if a not in claim_by or a==clid: die(path+".oracleSemanticClaims",f"invalid alternative {a}")
    answers=arr(t["answerKey"],path+".task.answerKey"); seen=set()
    for i,a0 in enumerate(answers):
        p=f"{path}.task.answerKey[{i}]"; a=obj(a0,p); keys(a,p,{"questionId","answer"},{"supportFactIds","supportClaimIds"}); q=text(a["questionId"],p+".questionId"); text(a["answer"],p+".answer",True)
        if q not in qids or q in seen:
            die(p+".questionId","unknown/duplicate")
        seen.add(q)
        n=0
        for field,known in (("supportFactIds",set(fact_by)),("supportClaimIds",set(claim_by))):
            if field in a:
                rs=strings(a[field],p+"."+field); n+=len(rs)
                if set(rs)-known: die(p+"."+field,"unknown FactIds" if field=="supportFactIds" else "unknown claimIds")
        if not n: die(p,"answer needs support")
    if seen!=set(qids): die(path+".task.answerKey","not exactly one answer per question")
    pr=obj(d["oracleDatasetProfile"],path+".oracleDatasetProfile"); keys(pr,path+".oracleDatasetProfile",{"profileVersion","entityIds","entityCount","factCount","repeatedRecordShape","commonPredicates","candidateRowLabelPredicate","candidateDimensions","technicalPredicates","mandatoryFactIds"})
    if pr["profileVersion"]!=PROFILE_SCHEMA: die(path+".oracleDatasetProfile.profileVersion","unexpected")
    entities=strings(pr["entityIds"],path+".oracleDatasetProfile.entityIds"); subjects=set(by_subject)
    if set(entities)!=subjects or integer(pr["entityCount"],path+".oracleDatasetProfile.entityCount",1)!=len(entities): die(path+".oracleDatasetProfile.entityIds","entity mismatch")
    if integer(pr["factCount"],path+".oracleDatasetProfile.factCount",1)!=len(fact_by): die(path+".oracleDatasetProfile.factCount","does not match canonicalFacts length")
    boolean(pr["repeatedRecordShape"],path+".oracleDatasetProfile.repeatedRecordShape")
    common=set.intersection(*(by_subject[x] for x in subjects))
    if set(strings(pr["commonPredicates"],path+".oracleDatasetProfile.commonPredicates",True))!=common: die(path+".oracleDatasetProfile.commonPredicates","intersection mismatch")
    row=pr["candidateRowLabelPredicate"]
    if row is not None:
        text(row,path+".oracleDatasetProfile.candidateRowLabelPredicate")
        if row not in common or not any(c["dataElement"]["id"]==row and c["facet"]=="display_role" and c["role"] in {"identifier","display_label"} and c["status"]=="supported" for c in claims): die(path+".oracleDatasetProfile.candidateRowLabelPredicate","unsupported row label")
    eligible=set(); ineligible=set(); dims={}
    for i,x0 in enumerate(arr(pr["candidateDimensions"],path+".oracleDatasetProfile.candidateDimensions")):
        p=f"{path}.oracleDatasetProfile.candidateDimensions[{i}]"; x=obj(x0,p); keys(x,p,{"predicate","semanticClaimIds","present","total","eligible"},{"ineligibilityReason"}); pred=text(x["predicate"],p+".predicate")
        if pred in dims or pred not in predicates or pred==row: die(p+".predicate","duplicate/unknown/row label")
        refs=strings(x["semanticClaimIds"],p+".semanticClaimIds")
        if any(r not in claim_by or claim_by[r]["dataElement"]["id"]!=pred for r in refs): die(p+".semanticClaimIds","invalid claim reference")
        present=sum(pred in by_subject[e] for e in subjects)
        if integer(x["present"],p+".present")!=present or integer(x["total"],p+".total",1)!=len(entities): die(p,"coverage count mismatch")
        if boolean(x["eligible"],p+".eligible"):
            if "ineligibilityReason" in x or any(claim_by[r]["status"]!="supported" for r in refs): die(p,"invalid eligible dimension")
            eligible.add(pred)
        else: text(x.get("ineligibilityReason"),p+".ineligibilityReason"); ineligible.add(pred)
        dims[pred]=x
    if set(strings(pr["technicalPredicates"],path+".oracleDatasetProfile.technicalPredicates",True))-predicates: die(path+".oracleDatasetProfile.technicalPredicates","unknown")
    mandatory=set(strings(pr["mandatoryFactIds"],path+".oracleDatasetProfile.mandatoryFactIds"))
    if mandatory!=set(fact_by): die(path+".oracleDatasetProfile.mandatoryFactIds","must equal all canonical FactIds exactly")
    ep=obj(d["expectedPresentation"],path+".expectedPresentation"); keys(ep,path+".expectedPresentation",{"acceptableDecisions","requiredRejectedCandidates","requiredCoveredFactIds","mustExposeFallback"},{"factsRequiredOnlyInFallback"})
    decisions=arr(ep["acceptableDecisions"],path+".expectedPresentation.acceptableDecisions"); selected=False; fallback_reasons=set()
    if not decisions: die(path+".expectedPresentation.acceptableDecisions","empty")
    for i,x0 in enumerate(decisions):
        p=f"{path}.expectedPresentation.acceptableDecisions[{i}]"; x=obj(x0,p); kind=text(x.get("kind"),p+".kind")
        if kind=="fallback": keys(x,p,{"kind","component","reason"});
        elif kind=="select":
            keys(x,p,{"kind","component","entityIds","rowLabelPredicate","dimensionPredicates","fallback"},{"excludedPredicates"}); selected=True
            if x["component"]!="comparison_table" or set(strings(x["entityIds"],p+".entityIds"))!=set(entities) or x["rowLabelPredicate"]!=row or set(strings(x["dimensionPredicates"],p+".dimensionPredicates"))!=eligible or x["fallback"]!="generic_property_sections": die(p,"invalid table selection")
            excluded=set()
            for j,z0 in enumerate(arr(x.get("excludedPredicates",[]),p+".excludedPredicates")):
                zp=f"{p}.excludedPredicates[{j}]"; z=obj(z0,zp); keys(z,zp,{"predicate","reason"}); excluded.add(text(z["predicate"],zp+".predicate")); text(z["reason"],zp+".reason")
            if excluded!=ineligible: die(p+".excludedPredicates","must equal ineligible dimensions")
            continue
        else: die(p+".kind","unsupported")
        if x["component"]!="generic_property_sections": die(p+".component","invalid fallback")
        fallback_reasons.add(text(x["reason"],p+".reason"))
    rejected=set()
    for i,x0 in enumerate(arr(ep["requiredRejectedCandidates"],path+".expectedPresentation.requiredRejectedCandidates")):
        p=f"{path}.expectedPresentation.requiredRejectedCandidates[{i}]"; x=obj(x0,p); keys(x,p,{"component","reason"}); pair=(text(x["component"],p+".component"),text(x["reason"],p+".reason"))
        if pair in rejected:
            die(p,"duplicate")
        rejected.add(pair)
    if not selected and any(("comparison_table",r) not in rejected for r in fallback_reasons): die(path+".expectedPresentation.requiredRejectedCandidates","fallback rejection missing")
    covered=set(strings(ep["requiredCoveredFactIds"],path+".expectedPresentation.requiredCoveredFactIds")); fallback=set(strings(ep.get("factsRequiredOnlyInFallback",[]),path+".expectedPresentation.factsRequiredOnlyInFallback",True))
    if (covered|fallback)!=mandatory or covered&fallback: die(path+".expectedPresentation","coverage plus fallback-only coverage must equal all facts and be disjoint")
    if not boolean(ep["mustExposeFallback"],path+".expectedPresentation.mustExposeFallback"): die(path+".expectedPresentation.mustExposeFallback","must be true")
    return cid

def validate_benchmark(root: Path, expected_manifest_sha256: str|None=FROZEN_MANIFEST_SHA256)->Summary:
    root=root.resolve()
    if not root.is_dir(): die(str(root),"not a directory")
    m,paths=validate_manifest(root,expected_manifest_sha256); ids=[]
    for rel,p in paths: ids.append(validate_case(read_json(p),rel))
    if len(ids)!=len(set(ids)) or ids!=m["caseIds"]: die("manifest.caseIds","duplicate or path-order mismatch")
    return Summary(m["benchmarkId"],len(ids),len(m["files"]))

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--root",type=Path,default=Path("experiments/presentation/semantic-planning-v0")); ap.add_argument("--json",action="store_true"); a=ap.parse_args(argv)
    try: r=validate_benchmark(a.root)
    except ValidationError as e: print(f"semantic-planning benchmark invalid: {e}",file=sys.stderr); return 1
    print(json.dumps(r.json(),ensure_ascii=False,sort_keys=True) if a.json else f"semantic-planning benchmark valid: {r.case_count} cases, {r.file_count} frozen files"); return 0
if __name__=="__main__": raise SystemExit(main())
