#!/usr/bin/env python3
"""Exact dependency-aware fusion runtime for DSL-D2."""
from __future__ import annotations
import subprocess, tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

class FusionError(RuntimeError): pass

def fraction(value: dict[str, Any]) -> Fraction:
    result = Fraction(int(value["numerator"]), int(value["denominator"]))
    if result < 0: raise FusionError("negative evidence is forbidden")
    return result

def text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"

def atom(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"

def policy(b: Fraction,d: Fraction,u: Fraction,p: Fraction,c: Fraction):
    if c >= Fraction(1,2): return "report_conflict","report_conflict",True
    if u >= Fraction(1,2): return "abstain_high_uncertainty","abstain",True
    if p >= Fraction(3,4) and b >= Fraction(1,2) and u <= Fraction(1,4): return "assert_with_evidence","answer_with_epistemic_profile",False
    if p <= Fraction(1,4) and d >= Fraction(1,2) and u <= Fraction(1,4): return "qualified_refutation","explain_refutation_with_profile",False
    if p >= Fraction(13,20) and b < Fraction(1,2) and u < Fraction(1,2): return "qualify_prior_sensitive","answer_with_prior_warning",False
    return "qualified_uncertain","answer_with_uncertainty",True

def blocked_frame(bundle: dict[str,Any], kind: str):
    missing=kind=="missing_dependency_metadata"
    return {"schemaVersion":"0.1","dslLevel":"DSL-D2","fusionId":bundle["fusionId"],"proposition":bundle["proposition"],
    "opinionSubjectLevel":bundle["opinionSubjectLevel"],"operatorPlan":"blocked_missing_dependency" if missing else "blocked_incompatible_base_rate",
    "sourceReportCount":len(bundle["reports"]),"dependencyGroupCount":0,"effectiveGroupCount":0,"exactPositiveEvidence":None,
    "exactNegativeEvidence":None,"exactOpinion":None,"exactProjectedProbability":None,"exactConflictIndex":None,
    "conclusion":"request_dependency_metadata" if missing else "request_compatible_base_rates",
    "action":"abstain_and_request_dependency_metadata" if missing else "abstain_and_request_compatible_base_rates",
    "withholdsAssertiveDecision":True,"dependencyMetadataComplete":not missing,"compatibleBaseRates":missing,
    "implicitFusionPerformed":False,"dependencyGroups":[],"provenance":sorted({p for r in bundle["reports"] for p in r["provenance"]}),
    "scope":{"kind":"local-pilot","snapshot":"D2-2026.08"},
    "warnings":["dependency-metadata-missing" if missing else "incompatible-base-rates","no-implicit-fusion","pilot-only"]}

def compute(bundle: dict[str,Any]):
    reports=bundle["reports"]
    if not reports: raise FusionError("at least one report is required")
    rates=[fraction(r["baseRate"]) for r in reports]
    if len(set(rates))!=1: return blocked_frame(bundle,"incompatible_base_rates"),None
    if any(not r.get("dependencyGroup") for r in reports): return blocked_frame(bundle,"missing_dependency_metadata"),None
    W=fraction(bundle["priorWeight"])
    if W<=0: raise FusionError("prior weight must be positive")
    groups={}
    for r in reports: groups.setdefault(r["dependencyGroup"],[]).append(r)
    if len(reports)==1: plan="single_source"
    elif len(groups)==1: plan="average_within_group"
    elif all(len(v)==1 for v in groups.values()): plan="cumulative_across_groups"
    else: plan="average_then_cumulative"
    R=S=Fraction(0); group_frames=[]
    for gid in sorted(groups):
        rows=groups[gid]
        gr=sum((fraction(r["positiveEvidence"]) for r in rows),Fraction(0))/len(rows)
        gs=sum((fraction(r["negativeEvidence"]) for r in rows),Fraction(0))/len(rows)
        R+=gr; S+=gs
        group_frames.append({"dependencyGroup":gid,"reportIds":sorted(r["reportId"] for r in rows),"sourceReportCount":len(rows),
        "operator":"single" if len(rows)==1 else "average","exactPositiveEvidence":text(gr),"exactNegativeEvidence":text(gs)})
    a=rates[0]; Z=R+S+W; b=R/Z; d=S/Z; u=W/Z; p=b+a*u
    c=Fraction(0) if R+S==0 else 2*min(R,S)/(R+S)
    conclusion,action,withholds=policy(b,d,u,p,c)
    warnings=["no-implicit-fusion","pilot-only"]
    if any(len(v)>1 for v in groups.values()): warnings.append("dependent-reports-averaged")
    if len(groups)>1: warnings.append("independent-groups-cumulatively-combined")
    if c>=Fraction(1,2): warnings.append("conflict-high")
    if bundle["opinionSubjectLevel"]=="answer": warnings.append("answer-level-opinion")
    frame={"schemaVersion":"0.1","dslLevel":"DSL-D2","fusionId":bundle["fusionId"],"proposition":bundle["proposition"],
    "opinionSubjectLevel":bundle["opinionSubjectLevel"],"operatorPlan":plan,"sourceReportCount":len(reports),
    "dependencyGroupCount":len(groups),"effectiveGroupCount":len(groups),"exactPositiveEvidence":text(R),"exactNegativeEvidence":text(S),
    "exactOpinion":{"belief":text(b),"disbelief":text(d),"uncertainty":text(u),"baseRate":text(a)},
    "exactProjectedProbability":text(p),"exactConflictIndex":text(c),"conclusion":conclusion,"action":action,
    "withholdsAssertiveDecision":withholds,"dependencyMetadataComplete":True,"compatibleBaseRates":True,
    "implicitFusionPerformed":False,"dependencyGroups":group_frames,"provenance":sorted({x for r in reports for x in r["provenance"]}),
    "scope":{"kind":"local-pilot","snapshot":"D2-2026.08"},"warnings":sorted(warnings)}
    return frame,{"positive":R,"negative":S,"belief":b,"disbelief":d,"uncertainty":u,"base_rate":a,"projected":p,"conflict":c}

def prolog_program(bundle,frame,exact):
    facts=[]
    for r in bundle["reports"]:
        g=r.get("dependencyGroup","__missing__"); R=fraction(r["positiveEvidence"]); S=fraction(r["negativeEvidence"]); A=fraction(r["baseRate"])
        facts.append(f"report({atom(g)},{R.numerator} rdiv {R.denominator},{S.numerator} rdiv {S.denominator},{A.numerator} rdiv {A.denominator}).")
    W=fraction(bundle["priorWeight"]); ep=atom(frame["operatorPlan"]); ec=atom(frame["conclusion"])
    checks=f"Plan == {ep}, Conclusion == {ec}"
    if exact:
        checks=", ".join([checks,f"R =:= {exact['positive'].numerator} rdiv {exact['positive'].denominator}",f"S =:= {exact['negative'].numerator} rdiv {exact['negative'].denominator}",f"B =:= {exact['belief'].numerator} rdiv {exact['belief'].denominator}",f"D =:= {exact['disbelief'].numerator} rdiv {exact['disbelief'].denominator}",f"U =:= {exact['uncertainty'].numerator} rdiv {exact['uncertainty'].denominator}",f"A =:= {exact['base_rate'].numerator} rdiv {exact['base_rate'].denominator}",f"P =:= {exact['projected'].numerator} rdiv {exact['projected'].denominator}",f"C =:= {exact['conflict'].numerator} rdiv {exact['conflict'].denominator}"])
    return f''':- set_prolog_flag(prefer_rationals,true).
:- use_module(library(lists)).
{chr(10).join(facts)}
prior_weight({W.numerator} rdiv {W.denominator}).
missing_dependency :- report('__missing__',_,_,_).
compatible_base_rate(A) :- findall(X,report(_,_,_,X),Xs), sort(Xs,[A]).
group_average(G,R,S) :- findall(X,report(G,X,_,_),Rs),sum_list(Rs,TR),length(Rs,N),R is TR/N,findall(Y,report(G,_,Y,_),Ss),sum_list(Ss,TS),S is TS/N.
sum_groups([],0,0).
sum_groups([G|Gs],R,S) :- group_average(G,R0,S0),sum_groups(Gs,R1,S1),R is R0+R1,S is S0+S1.
plan(Gs,N,P) :- length(Gs,C),(N=:=1->P=single_source;C=:=1->P=average_within_group;findall(G,report(G,_,_,_),All),sort(All,U),length(All,N),length(U,C)->P=cumulative_across_groups;P=average_then_cumulative).
policy(B,D,U,P,C,O) :- (C>=1 rdiv 2->O=report_conflict;U>=1 rdiv 2->O=abstain_high_uncertainty;P>=3 rdiv 4,B>=1 rdiv 2,U=<1 rdiv 4->O=assert_with_evidence;P=<1 rdiv 4,D>=1 rdiv 2,U=<1 rdiv 4->O=qualified_refutation;P>=13 rdiv 20,B<1 rdiv 2,U<1 rdiv 2->O=qualify_prior_sensitive;O=qualified_uncertain).
compute(Plan,R,S,B,D,U,A,P,C,O) :- (missing_dependency->Plan=blocked_missing_dependency,O=request_dependency_metadata,R=0,S=0,B=0,D=0,U=0,A=0,P=0,C=0;\+compatible_base_rate(_)->Plan=blocked_incompatible_base_rate,O=request_compatible_base_rates,R=0,S=0,B=0,D=0,U=0,A=0,P=0,C=0;compatible_base_rate(A),findall(G,report(G,_,_,_),All),sort(All,Gs),length(All,N),plan(Gs,N,Plan),sum_groups(Gs,R,S),prior_weight(W),Z is R+S+W,B is R/Z,D is S/Z,U is W/Z,P is B+A*U,(R+S=:=0->C=0;C is 2*min(R,S)/(R+S)),policy(B,D,U,P,C,O)).
main :- compute(Plan,R,S,B,D,U,A,P,C,Conclusion),{checks},writeln(ok),halt(0).
main :- halt(1).
:- initialization(main,main).
'''

def verify_prolog(bundle,frame,exact,swipl,timeout_seconds):
    with tempfile.TemporaryDirectory(prefix="dsl-d2-") as td:
        path=Path(td)/"verify.pl"; path.write_text(prolog_program(bundle,frame,exact),encoding="utf-8",newline="\n")
        p=subprocess.run([swipl,"-q","-f",str(path)],text=True,encoding="utf-8",capture_output=True,timeout=timeout_seconds)
    if p.returncode or p.stdout.strip()!="ok": raise FusionError(f"SWI-Prolog mismatch: stdout={p.stdout!r} stderr={p.stderr!r}")

def build_frame(bundle,reports_hash,swipl="swipl",timeout_seconds=60,skip_prolog=False):
    frame,exact=compute(bundle)
    if not skip_prolog: verify_prolog(bundle,frame,exact,swipl,timeout_seconds)
    frame["sourceHashes"]=[reports_hash]
    frame["runtime"]={"engine":"python" if skip_prolog else "python+swipl","verifiedArithmetic":exact is not None,"verifiedOperatorPlan":True,"verifiedPolicy":True,"verifiedAgainstPrologKernel":not skip_prolog}
    return frame
