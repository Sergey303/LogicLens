#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile, unittest
from copy import deepcopy
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[1]; TOOLS=REPO_ROOT/"tools"; sys.path.insert(0,str(TOOLS))
def load(name):
 s=importlib.util.spec_from_file_location(name,TOOLS/f"{name}.py"); assert s and s.loader; m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m); return m
claims=load("semantic_claims_artifact"); profile=load("dataset_profile_artifact")
def write(path,v): path.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def case_value(oracle_override=None, ambiguous=False, single=False):
 entities=["r1"] if single else ["r1","r2"]
 facts=[]
 for i,e in enumerate(entities,1):
  facts += [
   {"factId":f"f:{e}:id","subject":e,"predicate":"ex:id","object":{"kind":"literal","lexical":e.upper(),"literalKind":"plain","language":None,"datatype":None},"origins":["o"]},
   {"factId":f"f:{e}:status","subject":e,"predicate":"ex:status","object":{"kind":"literal","lexical":"active" if i==1 else "closed","literalKind":"plain","language":None,"datatype":None},"origins":["o"]},
  ]
 cs=[
  {"claimId":"c:id","dataElement":{"kind":"predicate","id":"ex:id"},"facet":"display_role","role":"identifier","status":"supported","evidence":[{"kind":"ontology_label","value":"Код"}],"alternatives":[]},
  {"claimId":"c:status","dataElement":{"kind":"predicate","id":"ex:status"},"facet":"value_role","role":"status","status":"possible" if ambiguous else "supported","evidence":[{"kind":"ontology_label","value":"Статус"}],"alternatives":[]},
 ]
 repeated=not single
 dims=[] if single else [{"predicate":"ex:status","semanticClaimIds":["c:status"],"present":2,"total":2,"eligible":not ambiguous,**({"ineligibilityReason":"required_semantic_claim_not_supported"} if ambiguous else {})}]
 oracle={"profileVersion":"dataset-profile-v0","entityIds":entities,"entityCount":len(entities),"factCount":len(facts),"repeatedRecordShape":repeated,"commonPredicates":["ex:id","ex:status"],"candidateRowLabelPredicate":"ex:id","candidateDimensions":dims,"technicalPredicates":[],"mandatoryFactIds":[f["factId"] for f in facts]}
 if oracle_override: oracle.update(oracle_override)
 return {"schemaVersion":"semantic-planning-benchmark-case-v0","caseId":"case","caseKind":"negative" if single else "positive","researchTargets":["dataset_profile"],"task":{"language":"ru","text":"Сравни статусы.","goal":"inspect_entity" if single else "compare","questions":[{"questionId":"q1","text":"Статус?"}],"answerKey":[{"questionId":"q1","answer":"active","supportFactIds":["f:r1:status"]}]},"canonicalFacts":facts,"ontologyEvidence":[{"element":{"kind":"predicate","id":"ex:id"},"labels":[{"language":"ru","text":"Код"}],"definitions":[]},{"element":{"kind":"predicate","id":"ex:status"},"labels":[{"language":"ru","text":"Статус"}],"definitions":[]}],"oracleSemanticClaims":cs,"oracleDatasetProfile":oracle,"expectedPresentation":{"acceptableDecisions":[{"kind":"fallback","component":"generic_property_sections","reason":"repeated_records_required"}] if single else [{"kind":"select","component":"comparison_table","entityIds":entities,"rowLabelPredicate":"ex:id","dimensionPredicates":["ex:status"] if not ambiguous else [],"excludedPredicates":[] if not ambiguous else [{"predicate":"ex:status","reason":"ambiguous"}],"fallback":"generic_property_sections"}],"requiredRejectedCandidates":[{"component":"comparison_table","reason":"repeated_records_required"}] if single else [],"requiredCoveredFactIds":[f["factId"] for f in facts],"mustExposeFallback":True}}
def benchmark(base, case):
 root=base/"b"; (root/"cases").mkdir(parents=True); (root/"README.md").write_text("# x\n",encoding="utf-8"); write(root/"cases/01.json",case); files=[]
 for rel in ["README.md","cases/01.json"]:
  data=(root/rel).read_bytes(); files.append({"path":rel,"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
 write(root/"manifest.json",{"schemaVersion":"semantic-planning-benchmark-manifest-v0","benchmarkId":"b","status":"frozen","researchSpecification":"x","caseCount":1,"caseIds":["case"],"mutationPolicy":"append-new-version-only","files":files}); return root
def claims_file(root,out):
 a=claims.build_artifact(root,"case",expected_manifest_sha256=None); out.write_bytes(claims.canonical_json_bytes(a)); return out
class T(unittest.TestCase):
 def test_exact_profile(self):
  with tempfile.TemporaryDirectory() as d:
   root=benchmark(Path(d),case_value()); cp=claims_file(root,Path(d)/"c.json"); a=profile.build_artifact(root,cp,expected_manifest_sha256=None); self.assertEqual(case_value()["oracleDatasetProfile"],a["profile"])
 def test_ambiguous_dimension_is_ineligible(self):
  case=case_value(ambiguous=True)
  computed=profile.compute_dataset_profile(case,case["oracleSemanticClaims"])
  self.assertFalse(computed["candidateDimensions"][0]["eligible"])
  self.assertEqual("required_semantic_claim_not_supported",computed["candidateDimensions"][0]["ineligibilityReason"])
 def test_single_entity_has_no_dimensions(self):
  with tempfile.TemporaryDirectory() as d:
   root=benchmark(Path(d),case_value(single=True)); cp=claims_file(root,Path(d)/"c.json"); a=profile.build_artifact(root,cp,expected_manifest_sha256=None); self.assertFalse(a["profile"]["repeatedRecordShape"]); self.assertEqual([],a["profile"]["candidateDimensions"])
 def test_profile_algorithm_is_independent_of_oracle_field(self):
  original=case_value()
  changed=deepcopy(original)
  changed["oracleDatasetProfile"]["factCount"]=99
  self.assertEqual(
   profile.compute_dataset_profile(original,original["oracleSemanticClaims"]),
   profile.compute_dataset_profile(changed,changed["oracleSemanticClaims"]),
  )
 def test_canonical_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   root=benchmark(Path(d),case_value()); cp=claims_file(root,Path(d)/"c.json"); a=profile.build_artifact(root,cp,expected_manifest_sha256=None); p=Path(d)/"p.json"; p.write_bytes(profile.canonical_json_bytes(a)); self.assertEqual(a,profile.verify_artifact(root,cp,p,expected_manifest_sha256=None))
 def test_altered_profile_rejected_even_rehashed(self):
  with tempfile.TemporaryDirectory() as d:
   root=benchmark(Path(d),case_value()); cp=claims_file(root,Path(d)/"c.json"); a=profile.build_artifact(root,cp,expected_manifest_sha256=None); a["profile"]["factCount"]=99; x=deepcopy(a); x.pop("artifactHash"); a["artifactHash"]=profile.artifact_hash(x); p=Path(d)/"p.json"; p.write_bytes(profile.canonical_json_bytes(a));
   with self.assertRaises(profile.DatasetProfileArtifactError): profile.verify_artifact(root,cp,p,expected_manifest_sha256=None)
 def test_input_claims_artifact_is_bound(self):
  with tempfile.TemporaryDirectory() as d:
   root=benchmark(Path(d),case_value()); cp=claims_file(root,Path(d)/"c.json"); a=profile.build_artifact(root,cp,expected_manifest_sha256=None); self.assertEqual(json.loads(cp.read_text())["artifactHash"],a["input"]["semanticClaimsArtifactHash"])
if __name__=="__main__": unittest.main()
