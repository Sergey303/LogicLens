#!/usr/bin/env python3
"""Trusted semantic validation for bounded model responses."""
from __future__ import annotations
import json
from copy import deepcopy
from typing import Any
from semantic_claims_llm_contract import ALLOWED_EVIDENCE, ALLOWED_FACETS, ALLOWED_STATUSES, SemanticClaimsLlmError, exact_keys, validate_string

def validate_evidence(item: Any, label: str, predicate: str, fact_by_id: dict[str, dict[str, Any]], predicates: set[str], visible_labels: set[str], datatypes_by_predicate: dict[str, set[str]], task_text: str) -> None:
    if not isinstance(item, dict):
        raise SemanticClaimsLlmError(f'{label} must be an object')
    kind = item.get('kind')
    if kind not in ALLOWED_EVIDENCE:
        raise SemanticClaimsLlmError(f'{label} has unsupported evidence kind: {kind}')
    if kind == 'fact_ids':
        exact_keys(item, {'kind', 'factIds'}, label)
        values = item['factIds']
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise SemanticClaimsLlmError(f'{label}.factIds must be a non-empty unique array')
        for fact_id in values:
            if fact_id not in fact_by_id:
                raise SemanticClaimsLlmError(f'{label} references an unknown FactId: {fact_id}')
        if not any((fact_by_id[fact_id]['predicate'] == predicate for fact_id in values)):
            raise SemanticClaimsLlmError(f'{label} must include evidence for its own predicate')
        return
    if kind == 'neighboring_predicates':
        exact_keys(item, {'kind', 'predicateIds'}, label)
        values = item['predicateIds']
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise SemanticClaimsLlmError(f'{label}.predicateIds must be a non-empty unique array')
        if any((value not in predicates for value in values)):
            raise SemanticClaimsLlmError(f'{label} references an unknown predicate')
        return
    exact_keys(item, {'kind', 'value'}, label)
    value = validate_string(item['value'], f'{label}.value')
    if kind == 'ontology_label' and value not in visible_labels:
        raise SemanticClaimsLlmError(f'{label} is not an exact visible ontology label')
    if kind == 'datatype' and value not in datatypes_by_predicate[predicate]:
        raise SemanticClaimsLlmError(f'{label} is not a visible datatype for {predicate}')
    if kind == 'task_text' and value not in task_text:
        raise SemanticClaimsLlmError(f'{label} is not an exact task.text substring')

def validate_response(case: dict[str, Any], response: dict[str, Any]) -> None:
    exact_keys(response, {'claims', 'unclassifiedPredicateIds'}, 'model response')
    claims = response['claims']
    unclassified = response['unclassifiedPredicateIds']
    if not isinstance(claims, list) or len(claims) > 64:
        raise SemanticClaimsLlmError('claims must be an array with at most 64 items')
    if not isinstance(unclassified, list) or len(unclassified) > 64:
        raise SemanticClaimsLlmError('unclassifiedPredicateIds must be an array with at most 64 items')
    facts = case['canonicalFacts']
    fact_by_id = {fact['factId']: fact for fact in facts}
    predicate_order: list[str] = []
    for fact in facts:
        if fact['predicate'] not in predicate_order:
            predicate_order.append(fact['predicate'])
    predicates = set(predicate_order)
    task_text = case['task']['text']
    visible_labels = {label['text'] for item in case['ontologyEvidence'] for label in item.get('labels', [])}
    datatypes_by_predicate: dict[str, set[str]] = {predicate: set() for predicate in predicates}
    for fact in facts:
        datatype = fact['object'].get('datatype')
        if datatype:
            datatypes_by_predicate[fact['predicate']].add(datatype)
    if len(unclassified) != len(set(unclassified)):
        raise SemanticClaimsLlmError('unclassifiedPredicateIds contains duplicates')
    for index, predicate in enumerate(unclassified):
        validate_string(predicate, f'unclassifiedPredicateIds[{index}]', 512)
        if predicate not in predicates:
            raise SemanticClaimsLlmError(f'unclassified predicate is not visible: {predicate}')
    claimed_predicates: list[str] = []
    normalized_claim_keys: set[tuple[str, str, str]] = set()
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise SemanticClaimsLlmError(f'claims[{index}] must be an object')
        exact_keys(claim, {'dataElement', 'facet', 'role', 'status', 'evidence', 'alternativeIndices'}, f'claims[{index}]')
        element = claim['dataElement']
        if not isinstance(element, dict):
            raise SemanticClaimsLlmError(f'claims[{index}].dataElement must be an object')
        exact_keys(element, {'kind', 'id'}, f'claims[{index}].dataElement')
        if element['kind'] != 'predicate' or element['id'] not in predicates:
            raise SemanticClaimsLlmError(f'claims[{index}] references an unknown predicate')
        predicate = element['id']
        claimed_predicates.append(predicate)
        facet = claim['facet']
        role = claim['role']
        status = claim['status']
        if facet not in ALLOWED_FACETS:
            raise SemanticClaimsLlmError(f'claims[{index}] has unsupported facet: {facet}')
        validate_string(role, f'claims[{index}].role', 64)
        if not role[0].islower() or any((ch not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for ch in role)):
            raise SemanticClaimsLlmError(f'claims[{index}].role must be lower_snake_case')
        if status not in ALLOWED_STATUSES:
            raise SemanticClaimsLlmError(f'claims[{index}] has unsupported status: {status}')
        key = (predicate, facet, role)
        if key in normalized_claim_keys:
            raise SemanticClaimsLlmError(f'duplicate semantic claim: {key}')
        normalized_claim_keys.add(key)
        evidence = claim['evidence']
        if not isinstance(evidence, list) or len(evidence) > 12:
            raise SemanticClaimsLlmError(f'claims[{index}].evidence must contain at most 12 items')
        if status in {'supported', 'possible'} and (not evidence):
            raise SemanticClaimsLlmError(f'claims[{index}] requires evidence for status {status}')
        for evidence_index, item in enumerate(evidence):
            validate_evidence(item, f'claims[{index}].evidence[{evidence_index}]', predicate, fact_by_id, predicates, visible_labels, datatypes_by_predicate, task_text)
        alternatives = claim['alternativeIndices']
        if not isinstance(alternatives, list) or len(alternatives) != len(set(alternatives)):
            raise SemanticClaimsLlmError(f'claims[{index}].alternativeIndices must be a unique array')
        for alternative in alternatives:
            if isinstance(alternative, bool) or not isinstance(alternative, int):
                raise SemanticClaimsLlmError(f'claims[{index}] alternative index must be an integer')
            if alternative < 0 or alternative >= len(claims) or alternative == index:
                raise SemanticClaimsLlmError(f'claims[{index}] has invalid alternative index {alternative}')
    for index, claim in enumerate(claims):
        for alternative in claim['alternativeIndices']:
            if index not in claims[alternative]['alternativeIndices']:
                raise SemanticClaimsLlmError(f'alternative relation must be symmetric between claims {index} and {alternative}')
            if claims[alternative]['dataElement'] != claim['dataElement']:
                raise SemanticClaimsLlmError('alternative claims must interpret the same data element')
    claimed = set(claimed_predicates)
    unknown = set(unclassified)
    overlap = claimed & unknown
    if overlap:
        raise SemanticClaimsLlmError(f'predicates cannot be both claimed and unclassified: {sorted(overlap)}')
    missing = predicates - claimed - unknown
    if missing:
        raise SemanticClaimsLlmError(f'response omitted visible predicates: {sorted(missing)}')

def extract_content(raw_response: dict[str, Any], output_tokens: int) -> tuple[dict[str, Any], dict[str, Any]]:
    if raw_response.get('done') is not True:
        raise SemanticClaimsLlmError('Ollama response is not complete')
    done_reason = raw_response.get('done_reason')
    eval_count = raw_response.get('eval_count')
    if done_reason == 'length' or (isinstance(eval_count, int) and eval_count >= output_tokens):
        raise SemanticClaimsLlmError('Ollama generation reached the reviewed output limit')
    message = raw_response.get('message')
    if not isinstance(message, dict) or not isinstance(message.get('content'), str):
        raise SemanticClaimsLlmError('Ollama response has no message.content string')
    content = message['content']
    try:
        value = json.loads(content)
    except json.JSONDecodeError as error:
        raise SemanticClaimsLlmError(f'model content is invalid JSON at line {error.lineno}, column {error.colno}; output is not repaired') from error
    if not isinstance(value, dict):
        raise SemanticClaimsLlmError('model content must decode to a JSON object')
    transport = {'responseModel': raw_response.get('model'), 'doneReason': done_reason, 'promptEvalCount': raw_response.get('prompt_eval_count'), 'evalCount': eval_count, 'totalDuration': raw_response.get('total_duration')}
    return (value, transport)

def convert_claims(case_id: str, response: dict[str, Any]) -> list[dict[str, Any]]:
    identifiers = [f'llm:{case_id}:{index + 1:03d}' for index in range(len(response['claims']))]
    converted: list[dict[str, Any]] = []
    for index, claim in enumerate(response['claims']):
        converted.append({'claimId': identifiers[index], 'dataElement': deepcopy(claim['dataElement']), 'facet': claim['facet'], 'role': claim['role'], 'status': claim['status'], 'evidence': deepcopy(claim['evidence']), 'alternatives': [identifiers[item] for item in claim['alternativeIndices']]})
    return converted
