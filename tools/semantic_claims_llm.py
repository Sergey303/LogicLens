#!/usr/bin/env python3
"""Prepare, run, import, verify, and score bounded LLM Semantic Claims experiments."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any
from active_epoch.hashing import append_field, canonical_json_bytes
from semantic_claims_artifact import FROZEN_MANIFEST_SHA256, SemanticClaimsArtifactError, load_case
import semantic_claims_baseline as baseline
from semantic_claims_llm_contract import REQUEST_SCHEMA_VERSION, DEFAULT_ENDPOINT, DEFAULT_MODEL, DEFAULT_CONTEXT_TOKENS, DEFAULT_OUTPUT_TOKENS, SemanticClaimsLlmError, build_prompt, build_request, exact_keys, response_schema, validate_endpoint, validate_request, validate_string, validate_token_budget, FORBIDDEN_PROMPT_KEYS
from semantic_claims_llm_validation import convert_claims, extract_content, validate_evidence, validate_response
SCHEMA_VERSION = 'semantic-claims-llm-candidate-v0'
EVALUATION_SCHEMA_VERSION = 'semantic-claims-llm-evaluation-v0'
HASH_DOMAIN = b'LogicLensSemanticClaimsLlmCandidate\x00'
EVALUATION_HASH_DOMAIN = b'LogicLensSemanticClaimsLlmEvaluation\x00'
HASH_VERSION = bytes((1,))

def sha256_prefixed(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()

def domain_hash(domain: bytes, value: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(HASH_VERSION)
    append_field(digest, canonical_json_bytes(value))
    return 'sha256:' + digest.hexdigest()

def read_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode('utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SemanticClaimsLlmError(f'cannot read {label} {path}: {error}') from error
    if not isinstance(value, dict):
        raise SemanticClaimsLlmError(f'{label} must be a JSON object: {path}')
    return (value, raw)

def build_candidate(benchmark_root: Path, case_id: str, model_response: dict[str, Any], *, model: str, seed: int, request: dict[str, Any], transport: dict[str, Any], expected_manifest_sha256: str | None=FROZEN_MANIFEST_SHA256) -> dict[str, Any]:
    try:
        summary, manifest_raw, case_path, case, case_raw = load_case(benchmark_root.resolve(), case_id, expected_manifest_sha256)
    except SemanticClaimsArtifactError as error:
        raise SemanticClaimsLlmError(f'cannot load frozen benchmark case: {error}') from error
    validate_request(case, request)
    if request['model'] != model or request['options']['seed'] != seed:
        raise SemanticClaimsLlmError('candidate producer does not match the exact LLM request')
    validate_response(case, model_response)
    request_raw = canonical_json_bytes(request)
    response_raw = canonical_json_bytes(model_response)
    payload: dict[str, Any] = {'schemaVersion': SCHEMA_VERSION, 'stage': 'llm-semantic-claims', 'benchmark': {'benchmarkId': summary.benchmark_id, 'manifestSha256': sha256_prefixed(manifest_raw), 'caseId': case_id, 'casePath': case_path, 'caseSha256': sha256_prefixed(case_raw)}, 'producer': {'kind': 'llm', 'provider': 'ollama', 'model': model, 'seed': seed, 'temperature': 0, 'promptSha256': sha256_prefixed(request['messages'][0]['content'].encode('utf-8')), 'requestSha256': sha256_prefixed(request_raw), 'responseSha256': sha256_prefixed(response_raw)}, 'inputPolicy': {'taskTextUsed': True, 'canonicalFactsUsed': True, 'ontologyEvidenceUsed': True, 'answerKeyUsed': False, 'oracleClaimsUsed': False, 'oracleProfileUsed': False, 'expectedPresentationUsed': False}, 'transport': deepcopy(transport), 'claims': convert_claims(case_id, model_response), 'unclassifiedPredicateIds': deepcopy(model_response['unclassifiedPredicateIds'])}
    payload['artifactHash'] = domain_hash(HASH_DOMAIN, payload)
    return payload

def validate_candidate_shape(candidate: dict[str, Any]) -> None:
    exact_keys(candidate, {'schemaVersion', 'stage', 'benchmark', 'producer', 'inputPolicy', 'transport', 'claims', 'unclassifiedPredicateIds', 'artifactHash'}, 'candidate')
    if candidate['schemaVersion'] != SCHEMA_VERSION or candidate['stage'] != 'llm-semantic-claims':
        raise SemanticClaimsLlmError('unsupported LLM Semantic Claims candidate')
    if candidate['producer'].get('kind') != 'llm' or candidate['producer'].get('provider') != 'ollama':
        raise SemanticClaimsLlmError('candidate producer must be exact Ollama LLM')
    expected_policy = {'taskTextUsed': True, 'canonicalFactsUsed': True, 'ontologyEvidenceUsed': True, 'answerKeyUsed': False, 'oracleClaimsUsed': False, 'oracleProfileUsed': False, 'expectedPresentationUsed': False}
    if candidate['inputPolicy'] != expected_policy:
        raise SemanticClaimsLlmError('candidate input policy does not preserve the experiment boundary')

def verify_candidate(benchmark_root: Path, request_path: Path, raw_response_path: Path, model_response_path: Path, candidate_path: Path, *, expected_manifest_sha256: str | None=FROZEN_MANIFEST_SHA256) -> dict[str, Any]:
    request, request_raw = read_object(request_path.resolve(), 'LLM request')
    raw_response, raw_response_raw = read_object(raw_response_path.resolve(), 'raw Ollama response')
    model_response, response_raw = read_object(model_response_path.resolve(), 'model response')
    candidate, candidate_raw = read_object(candidate_path.resolve(), 'LLM Semantic Claims candidate')
    validate_candidate_shape(candidate)
    if request_raw != canonical_json_bytes(request):
        raise SemanticClaimsLlmError('LLM request is not canonical JSON')
    if response_raw != canonical_json_bytes(model_response):
        raise SemanticClaimsLlmError('model response is not canonical JSON')
    extracted, transport = extract_content(raw_response, request['options']['num_predict'])
    if extracted != model_response:
        raise SemanticClaimsLlmError('model response does not exactly match raw Ollama message.content')
    transport['rawResponseSha256'] = sha256_prefixed(raw_response_raw)
    response_model = transport.get('responseModel')
    if response_model is not None and response_model != request['model']:
        raise SemanticClaimsLlmError('raw Ollama response model does not match request model')
    rebuilt = build_candidate(benchmark_root, candidate['benchmark']['caseId'], model_response, model=candidate['producer']['model'], seed=candidate['producer']['seed'], request=request, transport=transport, expected_manifest_sha256=expected_manifest_sha256)
    if candidate != rebuilt:
        raise SemanticClaimsLlmError('candidate does not exactly reproduce request and model response')
    if candidate_raw != canonical_json_bytes(candidate):
        raise SemanticClaimsLlmError('candidate JSON is valid but not canonical bytes')
    without_hash = deepcopy(candidate)
    recorded = without_hash.pop('artifactHash')
    if domain_hash(HASH_DOMAIN, without_hash) != recorded:
        raise SemanticClaimsLlmError('candidate artifactHash mismatch')
    return candidate

def candidate_response(candidate: dict[str, Any]) -> dict[str, Any]:
    id_to_index = {claim['claimId']: index for index, claim in enumerate(candidate['claims'])}
    claims: list[dict[str, Any]] = []
    for claim in candidate['claims']:
        try:
            alternatives = [id_to_index[item] for item in claim['alternatives']]
        except KeyError as error:
            raise SemanticClaimsLlmError(
                f'candidate references an unknown alternative claimId: {error.args[0]}'
            ) from error
        claims.append({'dataElement': deepcopy(claim['dataElement']), 'facet': claim['facet'], 'role': claim['role'], 'status': claim['status'], 'evidence': deepcopy(claim['evidence']), 'alternativeIndices': alternatives})
    return {'claims': claims, 'unclassifiedPredicateIds': deepcopy(candidate['unclassifiedPredicateIds'])}

def build_evaluation(benchmark_root: Path, candidate: dict[str, Any], *, expected_manifest_sha256: str | None=FROZEN_MANIFEST_SHA256) -> dict[str, Any]:
    case_id = candidate['benchmark']['caseId']
    try:
        summary, manifest_raw, case_path, case, case_raw = load_case(benchmark_root.resolve(), case_id, expected_manifest_sha256)
    except SemanticClaimsArtifactError as error:
        raise SemanticClaimsLlmError(f'cannot load frozen benchmark case: {error}') from error
    reconstructed = candidate_response(candidate)
    validate_response(case, reconstructed)
    metrics = baseline.evaluate_claims(case, candidate['claims'])
    evidence_total = sum(len(claim['evidence']) for claim in candidate['claims'])
    payload: dict[str, Any] = {'schemaVersion': EVALUATION_SCHEMA_VERSION, 'stage': 'llm-semantic-claims-evaluation', 'benchmark': {'benchmarkId': summary.benchmark_id, 'manifestSha256': sha256_prefixed(manifest_raw), 'caseId': case_id, 'casePath': case_path, 'caseSha256': sha256_prefixed(case_raw)}, 'candidateArtifactHash': candidate['artifactHash'], 'scorer': {'kind': 'trusted-deterministic', 'id': 'semantic-claims-baseline-scorer-v0'}, 'metrics': metrics, 'contractEvidenceValidity': {'valid': evidence_total, 'total': evidence_total, 'rate': 1.0 if evidence_total else 0.0}}
    payload['artifactHash'] = domain_hash(EVALUATION_HASH_DOMAIN, payload)
    return payload

def verify_evaluation(benchmark_root: Path, candidate_path: Path, evaluation_path: Path, *, expected_manifest_sha256: str | None=FROZEN_MANIFEST_SHA256) -> dict[str, Any]:
    candidate, candidate_raw = read_object(candidate_path.resolve(), 'candidate')
    evaluation, evaluation_raw = read_object(evaluation_path.resolve(), 'evaluation')
    validate_candidate_shape(candidate)
    if candidate_raw != canonical_json_bytes(candidate):
        raise SemanticClaimsLlmError('candidate is not canonical JSON')
    expected = build_evaluation(benchmark_root, candidate, expected_manifest_sha256=expected_manifest_sha256)
    if evaluation != expected:
        raise SemanticClaimsLlmError('evaluation does not exactly reproduce the trusted scorer')
    if evaluation_raw != canonical_json_bytes(evaluation):
        raise SemanticClaimsLlmError('evaluation JSON is valid but not canonical bytes')
    without_hash = deepcopy(evaluation)
    recorded = without_hash.pop('artifactHash')
    if domain_hash(EVALUATION_HASH_DOMAIN, without_hash) != recorded:
        raise SemanticClaimsLlmError('evaluation artifactHash mismatch')
    return evaluation

def write_new(path: Path, value: dict[str, Any], label: str) -> None:
    path = path.resolve()
    if path.exists():
        raise SemanticClaimsLlmError(f'{label} output already exists: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))

def load_frozen_case(root: Path, case_id: str):
    try:
        return load_case(root.resolve(), case_id, FROZEN_MANIFEST_SHA256)
    except SemanticClaimsArtifactError as error:
        raise SemanticClaimsLlmError(f'cannot load frozen benchmark case: {error}') from error

def prepare_command(args: argparse.Namespace) -> int:
    _, _, _, case, _ = load_frozen_case(args.benchmark_root, args.case_id)
    request = build_request(case, args.model, args.seed, args.context_tokens, args.output_tokens)
    write_new(args.output, request, 'request')
    print(f'Prepared bounded LLM request: {args.case_id}')
    print(f'Model: {args.model}')
    print(f'Request SHA-256: {sha256_prefixed(canonical_json_bytes(request))}')
    return 0

def import_command(args: argparse.Namespace) -> int:
    request, _ = read_object(args.request.resolve(), 'LLM request')
    raw_response, raw_response_raw = read_object(args.raw_response.resolve(), 'raw Ollama response')
    model_response, transport = extract_content(raw_response, request['options']['num_predict'])
    transport['rawResponseSha256'] = sha256_prefixed(raw_response_raw)
    response_model = transport.get('responseModel')
    if response_model is not None and response_model != request['model']:
        raise SemanticClaimsLlmError('raw Ollama response model does not match request model')
    write_new(args.model_response, model_response, 'model response')
    candidate = build_candidate(args.benchmark_root, args.case_id, model_response, model=request['model'], seed=request['options']['seed'], request=request, transport=transport)
    write_new(args.candidate, candidate, 'candidate')
    evaluation = build_evaluation(args.benchmark_root, candidate)
    write_new(args.evaluation, evaluation, 'evaluation')
    print(f'Imported LLM Semantic Claims candidate: {args.case_id}')
    print(f"Candidate hash: {candidate['artifactHash']}")
    return 0

def run_command(args: argparse.Namespace) -> int:
    validate_endpoint(args.endpoint)
    _, _, _, case, _ = load_frozen_case(args.benchmark_root, args.case_id)
    request = build_request(case, args.model, args.seed, args.context_tokens, args.output_tokens)
    output = args.output.resolve()
    if output.exists():
        raise SemanticClaimsLlmError(f'run output directory already exists: {output}')
    output.mkdir(parents=True)
    request_path = output / 'request.json'
    request_path.write_bytes(canonical_json_bytes(request))
    wire = deepcopy(request)
    wire.pop('schemaVersion')
    body = json.dumps(wire, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    http_request = urllib.request.Request(args.endpoint, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(http_request, timeout=args.timeout_seconds) as response:
            raw_bytes = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise SemanticClaimsLlmError(f'loopback Ollama request failed: {error}') from error
    raw_path = output / 'raw-ollama-response.json'
    raw_path.write_bytes(raw_bytes)
    args.request = request_path
    args.raw_response = raw_path
    args.model_response = output / 'model-response.json'
    args.candidate = output / 'candidate.json'
    args.evaluation = output / 'evaluation.json'
    return import_command(args)

def verify_command(args: argparse.Namespace) -> int:
    candidate = verify_candidate(args.benchmark_root, args.request, args.raw_response, args.model_response, args.candidate)
    print(f"Verified LLM Semantic Claims candidate: {candidate['benchmark']['caseId']}")
    print(f"Candidate hash: {candidate['artifactHash']}")
    return 0

def evaluate_command(args: argparse.Namespace) -> int:
    candidate, raw = read_object(args.candidate.resolve(), 'candidate')
    validate_candidate_shape(candidate)
    if raw != canonical_json_bytes(candidate):
        raise SemanticClaimsLlmError('candidate is not canonical JSON')
    evaluation = build_evaluation(args.benchmark_root, candidate)
    write_new(args.output, evaluation, 'evaluation')
    print(f"Evaluated LLM Semantic Claims candidate: {candidate['benchmark']['caseId']}")
    return 0

def verify_evaluation_command(args: argparse.Namespace) -> int:
    evaluation = verify_evaluation(args.benchmark_root, args.candidate, args.artifact)
    print(f"Verified LLM Semantic Claims evaluation: {evaluation['benchmark']['caseId']}")
    print(f"Evaluation hash: {evaluation['artifactHash']}")
    return 0

def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest='command', required=True)

    def common(item: argparse.ArgumentParser) -> None:
        item.add_argument('--benchmark-root', type=Path, default=Path('experiments/presentation/semantic-planning-v0'))
    prepare = sub.add_parser('prepare')
    common(prepare)
    prepare.add_argument('--case-id', required=True)
    prepare.add_argument('--model', default=DEFAULT_MODEL)
    prepare.add_argument('--seed', type=int, default=0)
    prepare.add_argument('--context-tokens', type=int, default=DEFAULT_CONTEXT_TOKENS)
    prepare.add_argument('--output-tokens', type=int, default=DEFAULT_OUTPUT_TOKENS)
    prepare.add_argument('--output', type=Path, required=True)
    prepare.set_defaults(handler=prepare_command)
    import_item = sub.add_parser('import')
    common(import_item)
    import_item.add_argument('--case-id', required=True)
    import_item.add_argument('--request', type=Path, required=True)
    import_item.add_argument('--raw-response', type=Path, required=True)
    import_item.add_argument('--model-response', type=Path, required=True)
    import_item.add_argument('--candidate', type=Path, required=True)
    import_item.add_argument('--evaluation', type=Path, required=True)
    import_item.set_defaults(handler=import_command)
    run = sub.add_parser('run')
    common(run)
    run.add_argument('--case-id', required=True)
    run.add_argument('--model', default=DEFAULT_MODEL)
    run.add_argument('--seed', type=int, default=0)
    run.add_argument('--context-tokens', type=int, default=DEFAULT_CONTEXT_TOKENS)
    run.add_argument('--output-tokens', type=int, default=DEFAULT_OUTPUT_TOKENS)
    run.add_argument('--endpoint', default=DEFAULT_ENDPOINT)
    run.add_argument('--timeout-seconds', type=float, default=180.0)
    run.add_argument('--output', type=Path, required=True)
    run.set_defaults(handler=run_command)
    verify = sub.add_parser('verify')
    common(verify)
    verify.add_argument('--request', type=Path, required=True)
    verify.add_argument('--raw-response', type=Path, required=True)
    verify.add_argument('--model-response', type=Path, required=True)
    verify.add_argument('--candidate', type=Path, required=True)
    verify.set_defaults(handler=verify_command)
    evaluate = sub.add_parser('evaluate')
    common(evaluate)
    evaluate.add_argument('--candidate', type=Path, required=True)
    evaluate.add_argument('--output', type=Path, required=True)
    evaluate.set_defaults(handler=evaluate_command)
    verify_eval = sub.add_parser('verify-evaluation')
    common(verify_eval)
    verify_eval.add_argument('--candidate', type=Path, required=True)
    verify_eval.add_argument('--artifact', type=Path, required=True)
    verify_eval.set_defaults(handler=verify_evaluation_command)
    return result

def main(argv: list[str] | None=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except SemanticClaimsLlmError as error:
        print(f'semantic claims LLM error: {error}', file=sys.stderr)
        return 1
if __name__ == '__main__':
    raise SystemExit(main())