# Local model runs

This directory is the default destination for representation-runner outputs.

Files matching `*.jsonl` and `*.summary.json` are intentionally ignored by Git. They contain raw local model responses, timing and token counters and can become large.

After reviewing a run:

1. keep the raw files locally or attach them to the corresponding Linear issue;
2. record only stable aggregate findings in `../runs.jsonl`;
3. include the Git commit, model name, quantization if known, mode, prompt hashes and benchmark version;
4. never commit secrets, private documents or unrelated Ollama conversations.
