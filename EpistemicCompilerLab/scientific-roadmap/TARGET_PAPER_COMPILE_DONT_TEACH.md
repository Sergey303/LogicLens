# Целевая флагманская статья LogicLens

Дата фиксации: 2026-08-05  
Статус: **обязательный научный контракт проекта**  
Приоритет: **единственная статья, усиливаемая до publication-grade уровня**  
Рабочая папка: `EpistemicCompilerLab/`  
Первая целевая площадка: **Transactions on Machine Learning Research (TMLR)**

## 1. Зафиксированное решение

До завершения этой работы LogicLens не распыляет основной исследовательский ресурс на отдельные статьи про:

- полный Epistemic DSL;
- selective routing как самостоятельную тему;
- privacy как самостоятельную тему;
- fuzzy membership;
- `belief / disbelief / uncertainty / base rate`;
- вероятность или opinion всего ответа;
- полноценное обучение весов Qwen;
- пользовательское HCI-исследование;
- production sandboxing.

Все релевантные компоненты используются только для усиления одной центральной причинной статьи.

## 2. Рабочее название

> **Compile, Don’t Teach: Verified Epistemic Interfaces for Fixed-Weight Small Language Models**

Русское рабочее название:

> **Компилировать, а не обучать: проверяемые эпистемические интерфейсы для малых языковых моделей с неизменяемыми весами**

Название может уточняться после основного HOLDOUT, но выражение `Compile, Don’t Teach` и противопоставление compilation versus contextual teaching должны сохраняться, если данные подтверждают центральную гипотезу.

## 3. Центральный научный тезис

Малые локальные языковые модели ненадёжно соблюдают формальную семантику, когда получают:

- исходные факты;
- исходную формальную программу;
- Prolog как текст;
- улучшенные сильным учителем инструкции;
- изменённое сильным учителем представление правил.

Они работают существенно надёжнее, если критическая формальная семантика предварительно выполнена доверенным runtime, а результат передан через закрытый типизированный verified decision frame.

Краткая формулировка:

> **Для фиксированных малых LLM проверяемая компиляция формального знания в типизированный интерфейс надёжнее, чем передача исходных данных, правил или улучшенных сильным учителем инструкций.**

Усиленная, но допустимая только после подтверждения всеми экспериментами формулировка:

> **Verified semantic compilation relocates formal reasoning from an unreliable language-model behaviour into an auditable runtime contract while preserving the language model as a local interpreter and renderer.**

## 4. Что статья не утверждает

Статья не должна утверждать, что:

- Codex обучил веса Qwen;
- Qwen научилась исполнять Prolog;
- любая LLM всегда выигрывает от symbolic runtime;
- LogicLens доказывает абсолютную приватность;
- один compiled frame решает все виды reasoning;
- Prolog является единственным подходящим formal runtime;
- perfect rendering следует из perfect frame;
- correctness формального вывода доказывает correctness source extraction;
- пилоты 18/18 и 24/24 уже являются publication-grade evidence.

Корректная граница:

> LogicLens исследует интерфейс между естественно-языковым компонентом и доверенным формальным исполнением при неизменяемых весах локального студента.

## 5. Почему эта тема выбрана

В репозитории уже наблюдалась причинно интересная последовательность результатов.

### 5.1. Prompt teacher не дал улучшения

Первый содержательный Codex→Qwen teacher-loop создал допустимое изменение prompt, но:

- TRAIN ухудшился с `4/6` до `3/6`;
- DEV сохранился на `3/6`;
- кандидат не был выбран;
- HOLDOUT остался у baseline.

Две последующие prompt-эпохи также не исправили ошибки.

Источник: [`../experiments/runs.jsonl`](../experiments/runs.jsonl).

### 5.2. Prolog teacher не дал улучшения

В Prolog-only треке:

- первая эпоха не исправила ни одного случая;
- вторая эпоха не исправила ни одного случая и создала регрессию;
- лучший результат остался у epoch 0;
- наблюдение показало, что Qwen читает Prolog как текст, но ненадёжно воспроизводит его операционную семантику.

Источник: [`../experiments/run-records/20260729T094212Z-teacher-loop-prolog.json`](../experiments/run-records/20260729T094212Z-teacher-loop-prolog.json).

### 5.3. Compiled decision frame дал 18/18

Детерминированный compiler:

1. извлёк обязательные поля;
2. выполнил SWI-Prolog;
3. сформировал закрытый decision frame;
4. передал Qwen только результат формальной части.

Frame oracle прошёл `18/18`, а Qwen правильно передала все четыре семантических поля в `18/18` случаях.

Источник: [`../experiments/run-records/20260729T105957Z-compiled-frame-control.json`](../experiments/run-records/20260729T105957Z-compiled-frame-control.json).

### 5.4. Frozen replication дала 24/24

На новых замороженных случаях:

- cases и parser были заморожены до student run;
- старые вопросы не передавались генератору;
- parser source не передавался генератору;
- frame correctness: `24/24`;
- rendering correctness: `24/24`;
- русский ответ: `24/24`.

Источник: [`../experiments/run-records/20260731T161003Z-compiled-frame-replication-v0.json`](../experiments/run-records/20260731T161003Z-compiled-frame-replication-v0.json).

Эти результаты являются только pilot evidence. Они обосновывают гипотезу, но не входят в новый frozen HOLDOUT как независимые данные.

## 6. Основной исследовательский вопрос

> **Какой интерфейс между формальным знанием и фиксированной малой LLM обеспечивает надёжное эпистемическое поведение: естественный текст, исходная формальная программа, инструкции сильного учителя или предварительно вычисленный verified frame?**

Вторичные вопросы:

1. На каких слоях возникают остаточные ошибки после compilation?
2. Какие поля decision frame действительно необходимы?
3. Сохраняется ли эффект на разных моделях, доменах и source families?
4. Может ли сильный внешний учитель улучшать capsule program без доступа к production data?
5. Когда compiled frame избыточен по сравнению с Direct или Full Context?

## 7. Формальная модель

### 7.1. Студент

Пусть:

```text
W = immutable student weights
```

Веса не изменяются между режимами и эпохами:

```text
hash(W_before) = hash(W_after)
```

Не используются:

- fine-tuning;
- LoRA;
- adapters;
- persistent conversational memory;
- запись данных в model files.

### 7.2. Capsule program

Состояние системы на эпохе `i`:

```text
C_i = {
  Sigma_i,
  P_i,
  E_i,
  G_i,
  V_i,
  T_i,
  Rho_i
}
```

где:

- `Sigma_i` — JSON Schema, ontology, predicate spaces;
- `P_i` — student prompts;
- `E_i` — extraction and normalization contracts;
- `G_i` — Epistemic DSL / Prolog modules;
- `V_i` — validators;
- `T_i` — tests and benchmark generators;
- `Rho_i` — routing and decision policy.

### 7.3. Данные

```text
S = sanitized teacher-visible development data
R = private production data not visible to the teacher
```

Teacher создаёт или оптимизирует program artifact:

```text
C* = TeacherOptimize(S, W)
```

Production inference выполняется локально:

```text
A = LocalInference(C*, W, R, u)
```

Обязательное ограничение:

```text
R not in TeacherView
```

Это архитектурное ограничение, а не заявление о формально доказанной differential privacy.

### 7.4. Pipeline

```text
source data
  -> candidate canonical JSONL
  -> schema / provenance / type validation
  -> Epistemic DSL / Core IR
  -> SWI-Prolog execution
  -> verified decision frame JSON
  -> fixed-weight local LLM rendering
```

Объекты должны оставаться раздельными:

1. source assertion;
2. user-request interpretation;
3. formal query;
4. derived epistemic status;
5. decision policy;
6. natural-language rendering.

## 8. Основные гипотезы

### H1 — Compilation advantage

`Compiled Frame` превосходит `Raw Prolog`, `Raw JSONL`, `Full Context`, `Prompt Teacher` и `Program Teacher` по primary metric на frozen HOLDOUT.

### H2 — Generalization

Compilation advantage сохраняется:

- на нескольких student model families;
- в нескольких предметных областях;
- на unseen source families;
- на unseen rule templates;
- на unseen entity families;
- на independently generated paraphrases.

### H3 — Error relocation

При корректном frame остаточные end-to-end ошибки концентрируются в слоях:

```text
natural language -> JSON query
verified frame -> final rendering
```

а не в deterministic formal execution.

### H4 — Contextual teaching limitation

Prompt editing или program editing сильным teacher не гарантируют улучшения фиксированного student и могут создавать регрессии.

H4 не требует доказать, что teacher editing никогда не работает. Требуется определить его средний эффект, variance и условия failure.

### H5 — Frame component necessity

Не все поля frame одинаково полезны. Ablation должна определить marginal value:

- `status`;
- `action`;
- `allowedConclusion`;
- `unknown` handling;
- `conflict` handling;
- `scope`;
- `provenance`;
- `warnings`;
- `proofTrace`.

### H6 — Privacy-bounded portability

Capsule program, разработанная по sanitized `S`, может применяться локально к необезличенным `R` того же declared domain contract без передачи `R` teacher.

H6 является secondary claim и не должна быть условием жизнеспособности основной статьи.

## 9. Publication-grade строгий subset

Первая статья использует только:

- explicit positive source assertions;
- explicit negative source assertions;
- `supported`;
- `refuted`;
- `unknown`;
- `conflicting`;
- version and scope;
- source provenance;
- dependency groups в минимально необходимой форме;
- safe strict logical rules;
- proof/evidence trace;
- deterministic decision policy;
- typed JSON request;
- typed JSON decision frame.

До завершения статьи исключаются:

- fuzzy membership;
- subjective opinions;
- calibrated probability;
- posterior distributions;
- credible intervals;
- credal sets;
- answer-level scalar probability;
- model training;
- persistent Prolog service.

## 10. Предметные области

Нужны минимум три домена с различной структурой знания.

### D1 — Versioned policies and governance

Содержит:

- роли;
- обязанности;
- локальные правила;
- versions;
- effective dates;
- exceptions;
- explicit conflicts;
- open-world unknown.

### D2 — Engineering specifications

Содержит:

- revisions;
- compatibility;
- mandatory fields;
- typed identifiers;
- thresholds;
- exceptions;
- outdated and current specifications.

### D3 — Scientific or technical classification

Содержит:

- support and opposition;
- incomplete evidence;
- conflicting sources;
- provenance;
- safe strict derivations;
- non-guessable procedurally generated controls.

Для каждого домена обязательны:

1. reproducible public-source subset;
2. procedurally generated non-guessable subset;
3. independent replication source family;
4. explicit source provenance;
5. frozen extraction and scoring contracts.

## 11. Размер benchmark

Целевой минимум:

```text
600 base scenarios
```

Распределение:

```text
200 per domain
```

Каждый base scenario может иметь несколько парафразов, но статистической единицей остаётся scenario, а не отдельный paraphrase.

Ожидаемый итоговый объём:

```text
1200-1800 natural-language questions
```

Split:

```text
TRAIN       35%
DEV         15%
HOLDOUT     25%
REPLICATION 25%
```

Разделение выполняется по группам, а не случайным вопросам:

- source family;
- predicate family;
- rule template;
- entity family;
- document version;
- paraphrase generator family.

## 12. Student models

Минимум четыре профиля:

1. модель около `2B-4B`;
2. модель около `7B-9B`;
3. модель около `12B-14B`;
4. независимое model family сопоставимого размера.

Qwen должна присутствовать как continuity model с pilot results.

Для каждого model profile фиксируются:

- exact model tag;
- provider/runtime version;
- model file hashes;
- quantization;
- context size;
- temperature;
- seed;
- token limits;
- hardware profile;
- prompt hash;
- schema hash.

## 13. Экспериментальные режимы

### M0 — Direct

Student получает только вопрос и answer schema.

### M1 — Full Context

Student получает вопрос и релевантные source facts в естественном или каноническом текстовом виде, но formal runtime не выполняется.

### M2 — Raw JSONL

Student получает canonical assertions JSONL без computed status.

### M3 — Raw Prolog

Student получает facts/rules как Prolog text и должен самостоятельно сформировать ответ.

### M4 — Prompt Teacher

Сильный teacher может менять только student prompt в рамках фиксированного бюджета и TRAIN-only feedback.

### M5 — Program Teacher

Сильный teacher может менять только formal representation в рамках фиксированного бюджета и TRAIN-only feedback.

### M6 — Compiled Frame

Trusted compiler и SWI-Prolog формируют decision frame. Student только интерпретирует и объясняет его.

### M7 — Oracle Frame

Student получает gold decision frame. Это верхняя граница renderer, а не deployable system.

### M8 — Direct Strong Teacher

Сильная модель отвечает сама. Этот режим измеряет ceiling и позволяет сравнить качество с amortized local pipeline.

## 14. Критические сравнения

Главное причинное сравнение:

```text
M6 - M3
```

Оно измеряет пользу исполнения formal semantics по сравнению с передачей той же программы как текста.

Сравнение compilation против contextual teaching:

```text
M6 - M4
M6 - M5
```

Качество compiler/query boundary:

```text
M7 - M6
```

Качество renderer:

```text
frame correctness - final answer correctness
```

Ценность formal execution сверх информации:

```text
M6 - M1
M6 - M2
```

Экономическая верхняя граница:

```text
M6 - M8
```

с отдельным учётом latency, tokens, hardware и teacher amortization.

## 15. Primary endpoint

Primary endpoint фиксируется до первого HOLDOUT run:

> **Exact Epistemic Contract Accuracy on frozen HOLDOUT**

Случай считается правильным, только если одновременно соблюдены все mandatory fields:

- правильный `status`;
- правильный `action`;
- правильные обязательные arguments;
- корректное различение `unknown`, `refuted`, `conflicting`;
- правильный version/scope;
- правильное clarification behaviour;
- отсутствие запрещённого вывода;
- отсутствие fabricated provenance.

Красивый текст не компенсирует нарушение formal contract.

## 16. Secondary metrics

### 16.1. Epistemic behaviour

- unknown-preservation rate;
- conflict-preservation rate;
- refuted-preservation rate;
- unsupported-certainty rate;
- scope-preservation accuracy;
- provenance precision/recall;
- forbidden-conclusion rate.

### 16.2. Query boundary

- predicate accuracy;
- argument linking accuracy;
- arity validity;
- semantic-ID validity;
- exact query match;
- acceptable alternative formalization;
- rejected-query recovery;
- clarification precision/recall.

### 16.3. Renderer

- frame-field preservation;
- frame-ignore rate;
- contradiction with frame;
- answer completeness;
- language compliance;
- fabricated evidence rate.

### 16.4. Efficiency

- end-to-end latency p50/p95;
- model input/output tokens;
- SWI-Prolog execution time;
- package verification time;
- cold and warm mode;
- RAM/VRAM;
- number of teacher calls;
- bytes of capsule program;
- quality-cost Pareto frontier.

## 17. Statistical protocol

Обязательно:

- paired evaluation: все modes видят одинаковые scenarios;
- hierarchical bootstrap по base scenarios;
- bootstrap confidence intervals;
- McNemar tests для paired binary outcomes;
- correction for multiple secondary comparisons;
- effect sizes;
- не менее трёх independent stochastic runs;
- fixed seeds там, где runtime поддерживает их честно;
- все malformed outputs считаются результатами;
- все excluded cases публикуются с заранее допустимой причиной;
- HOLDOUT используется один раз после выбора architecture;
- REPLICATION не используется для model selection.

Парафразы одного scenario не считаются независимыми наблюдениями.

## 18. Frame ablations

Ablation выполняются отдельно:

- удалить `allowedConclusion`;
- удалить `action`;
- удалить explicit `unknown` instruction;
- слить `unknown` и `refuted`;
- удалить `conflict`;
- удалить `scope`;
- удалить `provenance`;
- удалить `warnings`;
- удалить `proofTrace`;
- заменить descriptive field names короткими codes;
- передать frame без JSON Schema;
- передать raw tool output без normalized frame.

Если окажется, что почти весь эффект даёт только `allowedConclusion`, статья должна честно сузить вывод:

> Weak models benefit from a minimal executable decision contract rather than from exposure to the formal program itself.

Это допустимый и ценный результат.

## 19. Teacher protocol

Teacher:

- получает labeled TRAIN diagnostics;
- получает только aggregate DEV metrics;
- не получает DEV questions;
- не получает HOLDOUT;
- не получает REPLICATION;
- не получает private production data `R`;
- меняет только один declared factor в отдельном track;
- записывает hypothesis, expected effect и risk;
- не кодирует benchmark case IDs или полные вопросы;
- останавливается, когда reusable improvement не подтверждается.

Teacher не получает произвольный shell. Допустимый tool layer ограничен операциями вроде:

```text
run_student_on_sanitized_train
run_student_on_sanitized_dev
read_redacted_train_failures
read_aggregate_dev_metrics
propose_capsule_patch
run_deterministic_tests
```

Информационная граница должна обеспечиваться tooling, а не только инструкцией в prompt.

## 20. Fixed-weight и no-artifact contract

Student работает в inference-only режиме.

Перед и после каждой epoch проверяются:

```text
model file hashes
adapter directory
runtime cache policy
allowed output directories
unexpected file delta
```

Технически корректная формулировка:

> The student model weights are immutable, and the experiment creates no persistent model-side artifacts outside an explicit allowlist.

Нельзя утверждать, что данные не появляются в RAM/VRAM во время inference.

## 21. Privacy-bounded applied track

Privacy является вторичной экспериментальной осью.

### Teacher-visible sanitized data

```text
S = sanitized labeled data + sanitized question/error logs
```

### Teacher-hidden production data

```text
R = real private data
```

Teacher создаёт data-independent capsule program `C*` по `S`.

Локальный pipeline применяет `C*` к `R`:

```text
R
  -> local extraction
  -> jsonl(R)
  -> Epistemic DSL
  -> SWI-Prolog
  -> decision frame
  -> local rendering
```

Обезличенная капсула не деобезличивается. Вместо этого одна и та же program schema применяется заново к реальным local records.

Реальные display values могут храниться отдельно в local identity resolver. Formal runtime должен по возможности работать с internal IDs.

## 22. Reproducibility package

Публичный artifact должен содержать:

- source manifests;
- public and synthetic datasets;
- generation scripts;
- frozen scenarios;
- schemas;
- prompts;
- Epistemic DSL modules;
- compiled Prolog;
- validators;
- oracle;
- raw model outputs;
- model/runtime configs;
- scorers;
- statistical notebooks/scripts;
- hashes;
- rejected teacher candidates;
- runner failures;
- full error taxonomy;
- exact commands.

Model outputs остаются под `experiments/model-runs/` во время работы и публикуются только как reviewed artifact package.

## 23. Threats to validity

Статья должна заранее рассмотреть:

### 23.1. Frame contains the answer

Риск: student просто копирует готовый conclusion.

Защита:

- component ablations;
- tasks, где frame содержит verified premises, но renderer должен собрать содержательное объяснение;
- отдельная оценка frame compliance и answer quality;
- minimal-frame condition.

### 23.2. Synthetic benchmark dominance

Риск: результат не переносится на messy documents.

Защита:

- public real documents;
- source defects;
- revisions;
- ambiguous language;
- independent source-family replication.

### 23.3. One-model effect

Защита: минимум четыре model profiles и несколько families.

### 23.4. Closed teacher instability

Основной compilation effect должен быть teacher-agnostic. Codex используется как один teacher condition, но центральный вывод не должен зависеть от exact account-default model.

### 23.5. Parser overfitting

Защита:

- gold-query condition;
- extracted-query condition;
- split by templates and source families;
- frozen parser before HOLDOUT;
- independent replication.

### 23.6. Incorrect source extraction

Formal correctness не доказывает correctness assertions.

Защита:

- source-span binding;
- deterministic validation;
- extraction evaluation отдельно;
- provenance checks;
- human-reviewed subset.

### 23.7. Overclaiming privacy

Статья заявляет bounded interface and non-disclosure architecture, но не cryptographic or differential-privacy guarantee без отдельного формального исследования.

## 24. Stop and pivot criteria

### Центральный тезис сохраняется, если

`M6` статистически и практически превосходит `M3` минимум на двух model profiles и двух domains, а replication подтверждает направление эффекта.

### Тезис сужается, если

- эффект существует только у самых малых моделей;
- эффект определяется одним полем frame;
- Full Context почти равен Compiled Frame;
- gold frame работает, но extracted frame нет;
- compilation улучшает только `unknown/conflict`, но не general accuracy.

В этих случаях статья становится исследованием границ и failure modes, а не универсального преимущества.

### Маршрут прекращается, если

- `M6` не превосходит `M1/M2/M3` на независимом replication;
- frame compliance нестабилен у всех моделей;
- эффект исчезает после устранения benchmark leakage;
- основной результат объясняется прямым включением gold answer;
- source extraction error полностью доминирует и не локализуется.

Даже при прекращении маршрута все отрицательные результаты сохраняются как reviewed research artifacts, но не объявляются подтверждением центральной статьи.

## 25. Publication readiness gates

Статья не считается готовой к подаче, пока не выполнены все обязательные gates.

### G1 — Claim freeze

- title scope frozen;
- primary endpoint frozen;
- H1-H6 frozen;
- prohibited claims recorded.

### G2 — Benchmark freeze

- минимум 600 base scenarios;
- three domains;
- grouped splits;
- generation and source hashes;
- HOLDOUT sealed;
- REPLICATION sealed.

### G3 — System freeze

- schemas frozen;
- query contract frozen;
- frame contract frozen;
- scorer frozen;
- parser frozen before HOLDOUT;
- deterministic tests green.

### G4 — Model breadth

- four student profiles;
- at least two model families;
- exact hashes/configuration;
- three runs where stochastic.

### G5 — Baselines

- M0-M8 completed where applicable;
- no missing critical baseline;
- comparable token/context budgets documented.

### G6 — Ablations

- all critical frame ablations completed;
- gold versus extracted query separated;
- error layers separated.

### G7 — Replication

- independent sources/templates;
- frozen before evaluation;
- no tuning on replication;
- direction of primary effect reproduced.

### G8 — Artifact

- raw outputs preserved;
- scripts reproducible;
- failed calls published;
- exclusions justified;
- repository commands verified.

### G9 — Adversarial internal review

До подачи команда должна попытаться опровергнуть каждый abstract claim и записать:

- strongest alternative explanation;
- required control;
- result of control;
- remaining limitation.

## 26. План статьи

1. **Introduction** — проблема fixed-weight local LLM и formal semantics.
2. **Research question and contribution** — compilation versus contextual teaching.
3. **Related work** — tool use, neuro-symbolic systems, teacher-student prompting, knowledge compilation.
4. **System model** — assertions, query, runtime, frame, renderer.
5. **Experimental design** — domains, models, modes, splits.
6. **Primary results** — M6 versus M3/M4/M5.
7. **Error localization** — extraction, runtime, rendering.
8. **Frame ablations** — minimal sufficient interface.
9. **Generalization and replication**.
10. **Privacy-bounded applied track**.
11. **Efficiency and amortization**.
12. **Limitations and threats to validity**.
13. **Conclusion**.

## 27. Предварительный abstract contract

Каждое предложение будущего abstract должно иметь отдельное доказательство.

Черновой контракт:

1. Малые fixed-weight LLM часто нарушают formal semantics при получении raw programs.  
   **Доказательство:** M3 across models/domains.

2. Prompt/program editing strong teacher не обеспечивает стабильного улучшения.  
   **Доказательство:** M4/M5 controlled tracks.

3. Verified decision frames существенно повышают exact epistemic contract accuracy.  
   **Доказательство:** M6 versus baselines on HOLDOUT.

4. Эффект воспроизводится на unseen source/rule families.  
   **Доказательство:** REPLICATION.

5. Большая часть residual error локализуется на query and rendering boundaries.  
   **Доказательство:** gold/extracted decomposition and oracle frame.

6. Метод работает без изменения student weights и допускает privacy-bounded teacher interface.  
   **Доказательство:** hashes, artifact allowlist, sanitized teacher track.

Ни одно предложение не включается в final abstract без соответствующей таблицы или анализа.

## 28. Milestones

### M1 — Publication contract

- этот документ принят как source of truth;
- issue/task tree привязан к gates;
- scope creep запрещён.

### M2 — Benchmark schema

- unified case schema;
- domain adapters;
- grouped split tooling;
- leakage checks.

### M3 — Strict runtime subset

- safe logical rules;
- proof trace;
- batch query;
- cold/warm measurement;
- independent oracle.

### M4 — Baseline suite

- Direct;
- Full Context;
- Raw JSONL;
- Raw Prolog;
- Compiled Frame;
- Oracle Frame.

### M5 — Teacher tracks

- prompt-only;
- program-only;
- fixed budgets;
- TRAIN-only diagnostic loop;
- aggregate DEV.

### M6 — Multi-model pilot

- all student profiles;
- all domains;
- DEV only;
- error analysis;
- no HOLDOUT access.

### M7 — Freeze

- select final system;
- preregister primary endpoint;
- seal HOLDOUT and REPLICATION;
- freeze all hashes.

### M8 — HOLDOUT

- one execution;
- preserve every raw result;
- no post-hoc repair.

### M9 — REPLICATION

- independent execution;
- no tuning;
- analyze direction and effect size.

### M10 — Manuscript and artifact

- complete paper;
- complete reproducibility package;
- adversarial internal review;
- TMLR submission.

## 29. Первая целевая площадка и стратегия подачи

Первая цель: **TMLR**.

Причины выбора:

- работа является ML systems/behaviour study;
- центральный результат не обязан быть SOTA;
- отрицательные и диагностические результаты допустимы при строгой доказательной базе;
- rolling review позволяет отвечать на содержательные замечания;
- double blind уменьшает влияние академического статуса автора.

Резервный маршрут той же рукописи после содержательной переработки:

1. Journal of Web Semantics — только если усилена semantic/KG сторона;
2. Knowledge-Based Systems — если вклад формулируется как knowledge-based decision system;
3. SN Computer Science — как добротный широкий fallback.

Цель проекта — не обещать 100% принятия конкретным журналом, а довести одну рукопись до состояния, при котором вероятность публикации в хорошем международном журнале после последовательных подач максимально близка к практическому потолку.

## 30. Немедленное следующее решение

Следующий реализуемый шаг не относится к probabilities, fuzzy или расширению полного DSL.

Нужно зафиксировать и реализовать:

1. unified publication case schema;
2. exact epistemic contract scorer;
3. режимы `Direct`, `Full Context`, `Raw JSONL`, `Raw Prolog`, `Compiled Frame`, `Oracle Frame`;
4. gold-query versus extracted-query separation;
5. первый balanced multi-domain pilot без использования будущего HOLDOUT.

## 31. Короткая формула программы

```text
raw facts or program
        |
        v
fixed-weight small LLM                 -> unreliable formal behaviour

trusted semantic execution
        |
        v
verified typed frame
        |
        v
fixed-weight small LLM                 -> auditable local language behaviour
```

Главный объект исследования — не Prolog сам по себе и не способность Codex писать prompts.

Главный объект:

> **интерфейс, который переносит проверяемый результат формального рассуждения в поведение малой фиксированной языковой модели.**
