# Epoch 000 verification suite

These tests verify the reviewed zero-epoch package at three boundaries.

## Canonical data and generic view

- `data_contract_tests.pl` validates generated facts and provenance;
- `generic_view_tests.pl` validates labels, incoming/outgoing groups and source snapshots.

## Traversal identity and semantics

- `occurrence_identity_tests.pl` verifies OccurrenceId v1 canonical bytes and hashes independently of traversal enumeration;
- `subgraph_tests.pl` verifies depth 0/1/2, default edge eligibility, incoming/outgoing direction, repeated paths, cycles, deterministic ordering, and node/fact/occurrence/path limits.

## Process boundary

- `cli_internal_tests.pl` verifies internal timeout mapping;
- `tests/prolog_cli/run_cli_contract_tests.py` starts `entry.pl` as an external process, writes UTF-8 JSON to stdin, validates stdout against `contracts/prolog-cli-v0.schema.json`, and checks exit codes, deterministic bytes, output limits and the closed command surface.

The ontology package is generated into a temporary epoch before these tests run. The committed epoch remains `data-generated` until ENG-40 assembles and hashes the complete portable package.
