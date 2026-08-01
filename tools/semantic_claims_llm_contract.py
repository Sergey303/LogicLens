#!/usr/bin/env python3
"""Closed request and response contract for bounded Semantic Claims LLM runs."""
from __future__ import annotations
import json
import urllib.parse
from copy import deepcopy
from typing import Any
REQUEST_SCHEMA_VERSION = 'semantic-claims-llm-request-v0'
DEFAULT_ENDPOINT = 'http://127.0.0.1:11434/api/chat'
DEFAULT_MODEL = 'qwen2.5-coder:7b'
DEFAULT_CONTEXT_TOKENS = 2048
DEFAULT_OUTPUT_TOKENS = 1024
DEFAULT_NUM_GPU = 0
DEFAULT_NUM_BATCH = 64
ALLOWED_FACETS = {'display_role', 'value_role', 'policy_role'}
ALLOWED_STATUSES = {'supported', 'possible', 'unknown'}
ALLOWED_EVIDENCE = {'fact_ids', 'ontology_label', 'datatype', 'task_text', 'neighboring_predicates'}
FORBIDDEN_PROMPT_KEYS = {'answerKey', 'oracleSemanticClaims', 'oracleDatasetProfile', 'expectedPresentation'}

class SemanticClaimsLlmError(RuntimeError):
    pass

def response_schema() -> dict[str, Any]:
    evidence_variants = [{'type': 'object', 'additionalProperties': False, 'required': ['kind', 'factIds'], 'properties': {'kind': {'const': 'fact_ids'}, 'factIds': {'type': 'array', 'minItems': 1, 'uniqueItems': True, 'items': {'type': 'string', 'minLength': 1, 'maxLength': 256}}}}, {'type': 'object', 'additionalProperties': False, 'required': ['kind', 'value'], 'properties': {'kind': {'enum': ['ontology_label', 'datatype', 'task_text']}, 'value': {'type': 'string', 'minLength': 1, 'maxLength': 2000}}}, {'type': 'object', 'additionalProperties': False, 'required': ['kind', 'predicateIds'], 'properties': {'kind': {'const': 'neighboring_predicates'}, 'predicateIds': {'type': 'array', 'minItems': 1, 'uniqueItems': True, 'items': {'type': 'string', 'minLength': 1, 'maxLength': 512}}}}]
    claim = {'type': 'object', 'additionalProperties': False, 'required': ['dataElement', 'facet', 'role', 'status', 'evidence', 'alternativeIndices'], 'properties': {'dataElement': {'type': 'object', 'additionalProperties': False, 'required': ['kind', 'id'], 'properties': {'kind': {'const': 'predicate'}, 'id': {'type': 'string', 'minLength': 1, 'maxLength': 512}}}, 'facet': {'enum': sorted(ALLOWED_FACETS)}, 'role': {'type': 'string', 'pattern': '^[a-z][a-z0-9_]{0,63}$'}, 'status': {'enum': sorted(ALLOWED_STATUSES)}, 'evidence': {'type': 'array', 'maxItems': 12, 'items': {'oneOf': evidence_variants}}, 'alternativeIndices': {'type': 'array', 'uniqueItems': True, 'maxItems': 8, 'items': {'type': 'integer', 'minimum': 0, 'maximum': 63}}}}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': 'https://logiclens.local/contracts/semantic-claims-llm-response-v0.schema.json', 'title': 'LogicLens bounded LLM Semantic Claims response v0', 'type': 'object', 'additionalProperties': False, 'required': ['claims', 'unclassifiedPredicateIds'], 'properties': {'claims': {'type': 'array', 'maxItems': 64, 'items': claim}, 'unclassifiedPredicateIds': {'type': 'array', 'uniqueItems': True, 'maxItems': 64, 'items': {'type': 'string', 'minLength': 1, 'maxLength': 512}}}}

def public_case(case: dict[str, Any]) -> dict[str, Any]:
    task = case['task']
    return {'task': {'language': task['language'], 'goal': task['goal'], 'text': task['text'], 'questions': deepcopy(task.get('questions', []))}, 'canonicalFacts': deepcopy(case['canonicalFacts']), 'ontologyEvidence': deepcopy(case['ontologyEvidence'])}

def validate_token_budget(context_tokens: int, output_tokens: int) -> None:
    if isinstance(context_tokens, bool) or not 2048 <= context_tokens <= 32768:
        raise SemanticClaimsLlmError('context tokens must be an integer in 2048..32768')
    if isinstance(output_tokens, bool) or not 256 <= output_tokens <= 8192:
        raise SemanticClaimsLlmError('output tokens must be an integer in 256..8192')
    if output_tokens >= context_tokens:
        raise SemanticClaimsLlmError('output tokens must be smaller than context tokens')

def build_request(case: dict[str, Any], model: str, seed: int, context_tokens: int, output_tokens: int) -> dict[str, Any]:
    validate_token_budget(context_tokens, output_tokens)
    prompt = build_prompt(case)
    return {'schemaVersion': REQUEST_SCHEMA_VERSION, 'model': model, 'stream': False, 'format': response_schema(), 'messages': [{'role': 'user', 'content': prompt}], 'options': {'seed': seed, 'temperature': 0, 'num_ctx': context_tokens, 'num_predict': output_tokens, 'num_gpu': DEFAULT_NUM_GPU, 'num_batch': DEFAULT_NUM_BATCH}}

def exact_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = required - set(value)
    extra = set(value) - required
    if missing:
        raise SemanticClaimsLlmError(f'{label} missing keys: {sorted(missing)}')
    if extra:
        raise SemanticClaimsLlmError(f'{label} has unknown keys: {sorted(extra)}')

def validate_endpoint(endpoint: str) -> None:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        raise SemanticClaimsLlmError('Ollama endpoint must be an HTTP loopback URL')
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SemanticClaimsLlmError('Ollama endpoint must not contain credentials, query, or fragment')
    if parsed.path != '/api/chat':
        raise SemanticClaimsLlmError('Ollama endpoint path must be /api/chat')

def validate_request(case: dict[str, Any], request: dict[str, Any]) -> None:
    exact_keys(request, {'schemaVersion', 'model', 'stream', 'format', 'messages', 'options'}, 'LLM request')
    if request['schemaVersion'] != REQUEST_SCHEMA_VERSION:
        raise SemanticClaimsLlmError('unsupported LLM request schema')
    model = validate_string(request['model'], 'LLM request model', 256)
    if request['stream'] is not False:
        raise SemanticClaimsLlmError('LLM request must disable streaming')
    if request['format'] != response_schema():
        raise SemanticClaimsLlmError('LLM request response schema does not exactly match v0')
    messages = request['messages']
    if not isinstance(messages, list) or messages != [{'role': 'user', 'content': build_prompt(case)}]:
        raise SemanticClaimsLlmError('LLM request prompt does not exactly reproduce the frozen public case')
    options = request['options']
    if not isinstance(options, dict):
        raise SemanticClaimsLlmError('LLM request options must be an object')
    exact_keys(options, {'seed', 'temperature', 'num_ctx', 'num_predict', 'num_gpu', 'num_batch'}, 'LLM request options')
    seed = options['seed']
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 or (seed > 2147483647):
        raise SemanticClaimsLlmError('LLM request seed must be an integer in 0..2147483647')
    if options['temperature'] != 0:
        raise SemanticClaimsLlmError('LLM request temperature must be exactly zero')
    if options['num_gpu'] != DEFAULT_NUM_GPU or options['num_batch'] != DEFAULT_NUM_BATCH:
        raise SemanticClaimsLlmError('LLM request must preserve the CPU-safe Ollama profile')
    validate_token_budget(options['num_ctx'], options['num_predict'])
    if not model.strip():
        raise SemanticClaimsLlmError('LLM request model must not be blank')

def validate_string(value: Any, label: str, maximum: int=2000) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise SemanticClaimsLlmError(f'{label} must be a non-empty string up to {maximum} characters')
    return value

def build_prompt(case: dict[str, Any]) -> str:
    visible = public_case(case)
    serialized = json.dumps(visible, ensure_ascii=False, indent=2, sort_keys=True)
    for forbidden in FORBIDDEN_PROMPT_KEYS:
        if f'"{forbidden}"' in serialized:
            raise SemanticClaimsLlmError(f'forbidden field leaked into prompt: {forbidden}')
    return f'You are the Semantic Claims proposer inside a controlled LogicLens experiment.\n\nReturn only JSON matching the supplied response schema. Do not generate UI, choose a component, compute a dataset profile, or answer the task questions.\n\nFor every predicate in canonicalFacts, either emit one or more semantic claims or list the predicate exactly once in unclassifiedPredicateIds. Never invent or rename predicate IDs, FactIds, labels, datatypes, task text, or neighboring predicate IDs.\n\nFacets are display_role, value_role, or policy_role. Role strings are lower_snake_case interpretations; do not broaden a specific role merely to fit a vocabulary. Status is supported only when the visible evidence is sufficient, possible when multiple meanings remain plausible, and unknown when no interpretation is justified.\n\nEvidence must be machine-checkable and copied from the visible input:\n- fact_ids: existing FactIds only;\n- ontology_label: an exact visible label;\n- datatype: an exact visible datatype for the predicate;\n- task_text: an exact non-empty substring of task.text;\n- neighboring_predicates: existing predicate IDs only.\n\nA supported or possible claim must include evidence. Use alternativeIndices for mutually exclusive interpretations and make alternatives symmetric. Do not include confidence, probability, prose explanations, markdown, or fields absent from the schema.\n\nVISIBLE INPUT:\n{serialized}\n'
