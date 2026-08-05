# EngDoc DOCX local acceptance gate

ENG-145 requires one representative committed DOCX from the neighboring private
`Sergey303/EngDocSentinel` repository. The LogicLens Actions token cannot read that repository, so this
proof runs locally against the original bytes instead of copying opaque base64 between repositories.

## Source

Default path:

```text
D:\projects\ChatPilotGroup\EngDocSentinel\datasets\synthetic\demo-v0\generated\confirmed-power-conflict\01-technical-specification.docx
```

Expected source commit:

```text
916b19bf9a3047c1cb0e2bed9a1dab7bb084608a
```

Expected artifact SHA-256:

```text
bbd051dce7fd1e351175677c2c4c5bb8f14e2ba96c5a0f63298dd3a2f318023c
```

## Run

From the LogicLens repository root:

```powershell
.\services\document-evidence\verify-engdoc-docx.ps1
```

Use `-EngDocRoot` only when the neighboring repository is stored elsewhere. The runner:

1. verifies the source file SHA-256 before parsing;
2. executes all normal OOXML contracts;
3. checks EngDoc creator metadata and real engineering fields;
4. selects only the `Номинальная мощность: 120 W` paragraph;
5. exports that selection through `source-fragment-v0`;
6. proves that unselected DOCX blocks are not retained.

The ignored machine-readable proof is written to:

```text
.artifacts\document-evidence\engdoc-docx-local-proof-v0.json
```

Do not mark ENG-145 Done until this proof reports `status: passed` and its artifact SHA matches the value
above.
