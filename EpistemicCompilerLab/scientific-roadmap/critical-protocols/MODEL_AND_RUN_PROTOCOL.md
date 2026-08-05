# Model and Run Protocol
Статус: **MUST follow for every experiment**
## 1. Model profile
Register before first run:
```text
model_profile_id
exact tag
source/license
file hashes
quantization
runtime/version
context length
decoding parameters
seed policy
token limits
hardware
```
Changing any field creates a new profile.
Confirmatory minimum:
- four student profiles;
- at least two model families;
- Qwen continuity profile;
- one smaller and one larger profile.
## 2. Immutable student
Enforce:
- inference-only;
- model files read-only;
- no adapters/LoRA;
- no persistent conversation;
- no training API;
- explicit output allowlist;
- before/after hashes;
- unexpected-file scan.
Claim only that weights are unchanged and no persistent model-side artifacts exist outside allowlist.
## 3. Mode manifest
Every run identifies one mode M0–M14 and records:
```text
visible inputs
hidden inputs
allowed tools
prompt/schema/knowledge hashes
token budget
context budget
frame hash if applicable
```
A mode may not silently receive fields assigned to another mode.
## 4. Required matched controls
Confirmatory suite MUST include:
```text
M0 Direct
M1 Full Context
M2 Raw JSONL
M3 Raw Prolog
M6 Compiled Frame
M7 Oracle Frame
M9 Unstructured verified result
M10 Minimal verified label
M11 Deterministic renderer
M12 Frame without conclusion
M13 Corrupted frame
M14 Length/token-matched context
```
M4/M5 teacher modes support H4 but do not alone establish H1.
## 5. Run order
Use randomized blocked order by model/domain/scenario/mode/repeat.
Record:
```text
timestamps
cold/warm state
run/process ID
latency
token counts
exit status
raw stdout/stderr
hardware snapshot
```
Store raw output before scoring.
## 6. Retry rule
Freeze before confirmatory run:
```text
max attempts
retryable error codes
backoff
timeout
```
Never retry semantically wrong or malformed output.
All attempts remain stored.
## 7. M11 deterministic renderer
M11 consumes exactly the same frame as M6 and uses no LLM.
If M11 matches or exceeds M6 on all evaluated outcomes, manuscript MUST state that LLM rendering was unnecessary for this task class.
## 8. M13 corrupted frame
Corrupt one field at a time with mutation ID.
Measure:
```text
follow corruption
detect inconsistency
ignore frame
fabricate reconciliation
```
Do not mix corruptions in primary sensitivity analysis.
## 9. Batch validity gate
Batch is valid only if:
- frozen hashes match;
- all planned modes attempted;
- failures retained;
- no sealed-path access;
- no unexpected model artifact;
- scorer version matches;
- raw outputs immutable;
- completeness report passes.
Leakage or changed frozen hash invalidates affected confirmatory batch.
## 10. Execution STOP rules
STOP batch when:
- runtime config drifts;
- model hash changes;
- any mode sees hidden gold;
- partial results influence remaining order/config;
- provider behavior prevents matched comparison;
- output storage fails before scoring.
