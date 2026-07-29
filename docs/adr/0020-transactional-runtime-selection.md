# ADR-0020: Transactional runtime selection through current.json

## Status

Accepted for ENG-111.

## Context

ENG-107 introduced immutable runtime packages and an atomic `deployment/current.json` pointer. The activation transaction can commit revision 0.1 and retain revision 0.0 for rollback, but the existing local vertical-slice launcher still builds and opens a fresh zero-epoch package directly. A committed pointer has no operational effect if launchers continue to bypass it.

## Decision

The supported production launcher resolves the runtime only through `deployment/current.json`.

Selection is fail-closed:

1. validate the pointer with `active-pointer-v0`;
2. reproduce the domain-separated `pointerHash`;
3. reject any non-terminal transaction journal;
4. resolve exactly one safe relative path below `deployment/packages`;
5. reject symlinks, missing packages and path traversal;
6. validate the selected package manifest and every declared file hash;
7. for an activated pointer, require the transaction attestation named by `transactionId`, reproduce its `transactionHash` and require its final pointer to equal `current.json`;
8. require a regular, non-symlink `entry.pl`;
9. send pointer epoch and revision in every request;
10. reject a runtime response whose epoch or revision differs from the selected pointer.

`tools/run_transactional_runtime.py` is the narrow process launcher for direct Prolog requests. `tools/run_logiclens.py` is the supported API and web launcher. It resolves the selected package before building or starting services and passes the verified package path, epoch and revision to the API.

`tools/run_zero_epoch.py` remains an explicit historical and fixture workflow. It may build revision 0.0 for compatibility tests, but it is not the default production selection mechanism.

## Consequences

A committed activation now changes the package used by supported launchers without rewriting package bytes. Tampered pointers, stale generations, missing attestations, incomplete journals and modified packages stop startup before SWI-Prolog or the API is exposed.

Rollback remains an atomic pointer operation. When `current.json` is restored to the initial pointer, the same resolver selects and validates revision 0.0.
