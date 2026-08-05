# Полный путь к флагманской статье LogicLens и строгий аудит

Дата фиксации: 2026-08-05  
Статус: **обязательный операционный контракт**  
Связанный научный контракт: [`TARGET_PAPER_COMPILE_DONT_TEACH.md`](TARGET_PAPER_COMPILE_DONT_TEACH.md)  
Целевая статья: **Compile, Don’t Teach: Verified Epistemic Interfaces for Fixed-Weight Small Language Models**  
Первая целевая площадка: **Transactions on Machine Learning Research (TMLR)**

---

## 1. Назначение документа

`TARGET_PAPER_COMPILE_DONT_TEACH.md` фиксирует тему, тезис и научные границы статьи.

Этот документ фиксирует:

1. полный критический путь от текущего pilot evidence до подачи;
2. зависимости между этапами;
3. входы, выходы и обязательные gates каждого этапа;
4. критерии остановки, сужения тезиса и смены маршрута;
5. строгий red-team аудит текущего плана;
6. меры против утечки benchmark, круговой проверки и ложного усиления результата;
7. операционный путь подачи, рецензирования и повторной подачи;
8. окончательное определение publication-ready состояния.

Документ является source of truth для порядка работ. Немедленный следующий шаг не может отменять или заменять полный путь.

---

## 2. Строгий итоговый вердикт

Текущая исследовательская идея сильная, потому что уже наблюдается контраст:

- prompt teacher не улучшил Qwen;
- program/Prolog teacher не улучшил Qwen и создал регрессию;
- compiled decision frame дал `18/18`;
- frozen replication дала `24/24`.

Но текущий pilot ещё не доказывает центральный тезис публикационного уровня.

Наиболее опасные причины потенциального отказа:

1. сравнение `Compiled Frame` с `Raw Prolog` может быть признано тривиальным сравнением solver versus no solver;
2. frame может фактически содержать готовый ответ;
3. compiler, oracle и scorer могут разделять одну ошибочную реализацию;
4. benchmark может быть слишком синтетическим или слишком близким к известным шаблонам;
5. 600 scenarios пока являются целевым числом без power analysis;
6. один закрытый teacher и account-default model не воспроизводимы;
7. публичный именной репозиторий нельзя напрямую связать с double-blind submission;
8. extraction errors могут полностью поглотить эффект formal execution;
9. composite exact metric может скрывать, какой именно слой дал улучшение;
10. большое число режимов, моделей и метрик создаёт риск post-hoc выбора выгодного результата.

Следовательно, статья должна строиться не вокруг демонстрации системы, а вокруг строго разделённого причинного эксперимента.

---

## 3. Неподвижный центральный вопрос

> **Какой интерфейс между формальным знанием и fixed-weight small LLM обеспечивает надёжное эпистемическое поведение: исходный контекст, исходная программа, teacher-edited representation или предварительно вычисленный verified interface?**

Главная научная единица — не Prolog и не Codex.

Главная единица:

> **граница между trusted semantic execution и probabilistic language behaviour.**

---

## 4. Полный dependency graph

```text
P0  Governance and ownership
 |
 v
P1  Related-work and novelty map
 |
 v
P2  Claim/evidence contract
 |
 v
P3  Formal system contracts
 |
 +----------------------+
 |                      |
 v                      v
P4  Benchmark design    P5  Runtime/mode design
 |                      |
 v                      v
P6  Source acquisition  P7  Independent oracle/scorer
 |                      |
 +----------+-----------+
            |
            v
P8  Leakage-safe dataset build
            |
            v
P9  Small DEV-only calibration pilot
            |
            v
P10 Teacher tracks and matched controls
            |
            v
P11 Multi-model DEV study and power simulation
            |
            v
P12 Protocol freeze and preregistration
            |
            v
P13 One-shot HOLDOUT execution
            |
            v
P14 Independent REPLICATION
            |
            v
P15 Confirmatory analysis and red-team falsification
            |
            v
P16 Manuscript and claims audit
            |
            v
P17 Anonymous reproducibility artifact
            |
            v
P18 TMLR submission and review response
            |
            v
P19 Revision / resubmission / venue adaptation
```

Нельзя перескакивать к HOLDOUT до закрытия всех зависимостей P0–P12.

---

# Часть I. Полный путь

## P0 — Governance, ответственность и защита scope

### Цель

Превратить исследование из набора экспериментов в управляемый научный проект.

### Обязательные действия

- назначить одного владельца central claim;
- назначить владельца benchmark;
- назначить владельца runtime/oracle;
- назначить владельца statistical analysis;
- вести decision log;
- каждое изменение scope оформлять отдельным ADR/research decision;
- запретить включение fuzzy, probability, full subjective logic и model training до завершения статьи;
- сохранить все отрицательные результаты и rejected candidates.

### Выходы

```text
scientific-roadmap/decisions/
scientific-roadmap/claim-evidence-matrix.md
scientific-roadmap/risk-register.md
```

### Gate P0

- роли и ответственность записаны;
- центральный тезис один;
- запрещённые claims записаны;
- существует change-control процесс.

### Блокирующий провал

Если любой новый компонент нельзя связать с H1–H6 или threat-to-validity control, он не входит в текущую статью.

---

## P1 — Systematic related-work and novelty map

### Почему этап обязателен

Даже технически правильная работа может быть отклонена за неверное заявление новизны или отсутствие различия с:

- neuro-symbolic tool use;
- program-aided language models;
- toolformer/tool-use routing;
- teacher–student prompting;
- knowledge distillation;
- verifier-guided generation;
- structured output and constrained decoding;
- knowledge compilation;
- local/private LLM systems;
- executable semantic parsing.

### Действия

Для каждой близкой работы записать:

```text
problem
student model
teacher model
weights changed?
formal runtime executed?
student sees raw program or result?
privacy boundary
benchmark scale
main causal comparison
reported limitations
```

Создать матрицу отличий, а не обычный список ссылок.

### Обязательные вопросы

1. Есть ли уже работа, сравнивающая prompt teaching, program teaching и compiled interface?
2. Есть ли работа, где small LLM получает verified epistemic status с `unknown/refuted/conflicting`?
3. Есть ли работа, отделяющая query extraction, deterministic execution и rendering?
4. Есть ли работа с fixed-weight private student и teacher-visible sanitized development data?
5. Является ли наш результат новым методом или новым систематическим behavioural finding?

### Выходы

```text
research/related-work-map.csv
research/novelty-claims.md
research/closest-work-threats.md
```

### Gate P1

Каждое слово `new`, `first`, `novel`, `unprecedented` либо подтверждено обзором, либо удалено.

### Pivot

Если почти идентичная работа уже опубликована, статья переориентируется на:

- rigorous replication;
- failure boundary study;
- privacy-bounded deployment;
- epistemic-state preservation.

---

## P2 — Claim/evidence matrix

### Цель

До создания большого benchmark связать каждое будущее утверждение с конкретным экспериментом.

### Формат

| Claim | Primary/secondary | Treatment | Baseline | Unit | Metric | Required control | Failure wording |
|---|---|---|---|---|---|---|---|
| M6 лучше M3 | Primary | Compiled Frame | Raw Prolog | base scenario | exact contract | matched information | сузить до отдельных состояний |
| effect generalizes | Primary | M6 | strongest baseline | source/rule family | hierarchical effect | replication | ограничить область |
| teacher editing unstable | Secondary | M4/M5 | epoch 0 | scenario × epoch | delta/regression | fixed budget | описать как pilot-only |
| weights unchanged | Technical | inference pipeline | pre-run hash | model artifact | exact hash | read-only mount | убрать claim |
| privacy-bounded interface | Secondary | sanitized tooling | full-data oracle on public simulation | packet | disclosure audit | canaries | не заявлять privacy guarantee |

### Обязательное правило

Ни одно новое предложение в abstract не появляется после HOLDOUT, если его claim/evidence row не был заморожен заранее.

### Gate P2

- central claim имеет один primary endpoint;
- все secondary claims явно отмечены;
- для каждого claim записана допустимая формулировка при null result.

---

## P3 — Formal system contracts

### Цель

Заморозить смысл объектов до benchmark generation.

### Обязательные независимые контракты

1. source assertion;
2. provenance reference;
3. request interpretation;
4. JSON query;
5. query validation result;
6. Core IR;
7. SWI-Prolog execution result;
8. epistemic status;
9. decision policy;
10. decision frame;
11. rendered answer;
12. scoring record.

### Необходимые статусы

```text
supported
refuted
unknown
conflicting
invalid_query
needs_clarification
runtime_error
```

`runtime_error` нельзя превращать в `unknown`.

### Обязательные инварианты

- missing support не означает `refuted`;
- `refuted` требует explicit negative evidence;
- `conflicting` сохраняет обе стороны;
- decision не является world fact;
- formal proof не доказывает source extraction correctness;
- renderer не может расширять `allowedConclusion`;
- каждый evidence ID разрешается до source span или synthetic provenance;
- malformed query не оценивается как semantic unknown.

### Выходы

```text
schemas/publication-case.schema.json
schemas/query.schema.json
schemas/decision-frame.schema.json
schemas/score-record.schema.json
research/semantic-invariants.md
```

### Gate P3

- schemas проходят negative tests;
- каждое поле имеет однозначную семантику;
- backward-incompatible изменения после freeze запрещены.

---

## P4 — Benchmark design and statistical power

### Строгое исправление исходного плана

`600 base scenarios` — не доказанный размер, а первоначальный потолочный ориентир.

Финальный размер определяется до production generation через:

1. smallest effect size of interest;
2. pilot variance;
3. expected baseline accuracy;
4. clustering by scenario/domain/model;
5. desired power не ниже `0.90` для primary contrast;
6. simulation of hierarchical bootstrap/McNemar behaviour;
7. резерв на invalid outputs и инфраструктурные failures.

### Primary estimand

```text
Delta_primary = Accuracy(M6) - Accuracy(strongest matched non-executed baseline)
```

Недостаточно сравнить только с M3. Strongest baseline определяется на DEV и замораживается до HOLDOUT.

### Smallest effect of interest

До анализа задаётся минимальный practically meaningful gain, например:

```text
absolute +5 percentage points
```

Конкретное значение выбирается по стоимости и риску ошибочного formal behaviour, а не после просмотра HOLDOUT.

### Unit of analysis

Primary unit:

```text
base scenario
```

Парафразы, модели и повторы являются вложенными измерениями.

### Обязательные strata

- domain;
- epistemic status;
- rule depth;
- source family;
- query difficulty;
- extraction difficulty;
- scope/version difficulty;
- conflict/unknown cases.

### Gate P4

- существует simulation notebook;
- размер dataset обоснован power analysis;
- primary contrast один;
- family-wise secondary comparisons заранее определены.

---

## P5 — Runtime and experimental mode design

### Базовые режимы

Сохраняются M0–M8 из целевого контракта.

### Обязательные дополнительные matched controls

Исходный план недостаточно защищён от возражения «frame просто содержит ответ». Добавляются:

#### M9 — Verified result as unstructured text

Тот же trusted execution, но результат передаётся как обычный текст без typed frame.

Показывает ценность структуры интерфейса сверх самого solver result.

#### M10 — Minimal verified label

Student получает только status/action без provenance, proof и warnings.

Показывает, сводится ли эффект к копированию класса.

#### M11 — Deterministic template renderer

Decision frame преобразуется в ответ без LLM.

Показывает, нужна ли LLM вообще для рассматриваемых задач.

#### M12 — Frame with verified premises but no final conclusion

Frame содержит проверенные premises/evidence, но не `allowedConclusion`.

Проверяет способность student выполнять ограниченную композицию без raw formal execution.

#### M13 — Corrupted-frame sensitivity

Контролируемо искажаются отдельные поля frame.

Показывает, следует ли student frame или игнорирует его.

#### M14 — Length- and token-matched context

Контекст выравнивается по длине с frame.

Исключает объяснение эффекта меньшим количеством токенов.

### Ключевые причинные сравнения

```text
M6 vs M9   typed structure effect
M6 vs M10  rich frame marginal value
M6 vs M11  value of LLM renderer
M6 vs M12  value of explicit conclusion
M6 vs M14  non-length explanation
M9 vs M3   execution result effect independent of JSON structure
```

### Gate P5

Ни один основной вывод не опирается на сравнение, где treatment одновременно меняет несколько неконтролируемых факторов.

---

## P6 — Domain and source acquisition

### Домены

Сохраняются:

- D1 versioned policies;
- D2 engineering specifications;
- D3 scientific/technical classification.

### Требования к каждому домену

- минимум две независимые public source families;
- лицензия позволяет исследовательское распространение либо публикуются только derived artifacts;
- реальные messy documents, не только generated JSON;
- versions, missing data, explicit contradictions;
- non-guessable synthetic controls;
- source span addressing;
- отдельный replication source family.

### Запрещено

- создавать все domains одним LLM prompt;
- использовать одинаковые templates с переименованными сущностями;
- включать в HOLDOUT документы, которые использовались для разработки parser;
- включать claims, зависящие от спорной экспертной интерпретации без adjudication.

### Gate P6

- provenance manifest полный;
- licensing review пройден;
- source-family independence документирована;
- replication sources не использовались разработчиками runtime.

---

## P7 — Independent oracle and scorer

### Главная угроза

Если compiler, oracle и scorer используют одну реализацию, `24/24` может лишь показывать внутреннюю согласованность одной программы.

### Обязательная независимость

Нужны минимум два пути:

```text
Implementation A: production compiler + SWI-Prolog
Implementation B: independent oracle/scorer
```

Implementation B не должна импортировать production predicates или expected output generation.

Дополнительно:

- human-reviewed audit sample;
- mutation testing;
- property-based tests;
- intentionally incorrect frames;
- intentionally incorrect provenance;
- differential test between A and B;
- disagreements блокируют freeze.

### Human adjudication

Для неоднозначных public-source cases:

- два независимых annotator decisions;
- blinded disagreement review;
- adjudication rule;
- agreement statistic;
- ambiguous cases либо исключаются по заранее заданному правилу, либо получают несколько допустимых formalizations.

### Gate P7

- oracle independence доказана code dependency audit;
- mutation suite ловит каждую критическую ошибку;
- scorer не принимает gold leakage;
- human audit не выявляет систематическую ошибку semantics.

---

## P8 — Leakage-safe dataset build

### Split создаётся до tuning

Групповое разделение выполняется до teacher optimization и prompt tuning.

### Раздельные секреты

```text
TRAIN: visible to teacher where allowed
DEV: content hidden from teacher, aggregates visible
HOLDOUT: sealed
REPLICATION: separately sealed and independently sourced
```

### Leakage audit

Проверяются:

- exact duplicate;
- normalized duplicate;
- semantic near-duplicate;
- shared source paragraph;
- shared rule template;
- shared entity graph;
- shared generated paraphrase seed;
- benchmark IDs in prompts;
- expected fields in logs;
- accidental inclusion in repository search/RAG indexes;
- contamination через teacher packet.

### Canary tests

В HOLDOUT и REPLICATION добавляются non-semantic canary markers. Любое появление markers в teacher-visible artifacts означает утечку и аннулирует run.

### Gate P8

- split manifest hashed;
- leakage report clean;
- teacher tools технически не могут читать sealed paths;
- sealed data не индексируется локальными RAG/dev tools.

---

## P9 — DEV-only calibration pilot

### Назначение

Проверить инфраструктуру и измеримость эффекта, не оценивая финальный claim.

### Разрешено

- исправлять runner failures;
- уточнять schema diagnostics;
- исправлять scorer bugs;
- оценивать floor/ceiling;
- удалять заведомо неразличимые modes до freeze;
- оценивать runtime budget.

### Запрещено

- смотреть HOLDOUT;
- переносить specific DEV answers в prompts/rules;
- выбирать primary metric по максимальному observed effect;
- менять domain после просмотра его HOLDOUT.

### Выходы

- error taxonomy;
- pilot variance;
- power simulation inputs;
- final list of modes;
- final smallest effect of interest;
- infrastructure failure policy.

### Gate P9

- ни один mode не находится полностью на floor или ceiling во всех strata;
- scorer выдаёт объяснимые errors;
- средний runtime позволяет выполнить frozen experiment;
- compute budget подтверждён.

---

## P10 — Teacher tracks

### Строгий принцип

Teacher tracks являются secondary evidence. Основной compilation effect должен воспроизводиться без зависимости от закрытого teacher.

### Teacher conditions

- Codex prompt-only;
- Codex program-only;
- при возможности второй independent teacher family;
- human expert baseline;
- no-teacher epoch 0.

### Budget matching

Для каждого teacher:

- одинаковое число epochs;
- одинаковый input token budget;
- одинаковый allowed change size;
- одинаковые TRAIN diagnostics;
- одинаковые aggregate DEV metrics;
- одинаковое stop rule.

### Запрещено

- account-default без recorded resolved model identity, если её можно определить;
- teacher access к arbitrary shell;
- teacher access к DEV questions;
- combined prompt+program изменения до завершения isolated tracks;
- выбирать лучший teacher по HOLDOUT.

### Teacher instability reporting

Публикуются:

- accepted proposals;
- rejected proposals;
- regressions;
- zero-effect epochs;
- invalid candidates;
- tool errors;
- token and cost usage.

### Gate P10

Teacher claims формулируются только на основании нескольких runs/teachers либо явно называются case study.

---

## P11 — Multi-model DEV study and power confirmation

### Model matrix

Минимум:

- Qwen small;
- Qwen medium;
- Qwen larger local profile;
- independent model family.

### Обязательная проверка

- models действительно помещаются в declared hardware constraints;
- quantization recorded;
- deterministic settings checked;
- unsupported seeds не объявляются reproducible;
- repeated stochastic runs независимы;
- prompt adaptation minimal and declared.

### Analysis до freeze

- estimate baseline accuracy;
- estimate intra-scenario correlation;
- estimate model/domain heterogeneity;
- choose strongest matched baseline;
- update sample-size simulation without touching HOLDOUT;
- freeze subgroup analysis list.

### Gate P11

Есть evidence, что primary comparison не является floor/ceiling artefact и имеет достаточную мощность.

---

## P12 — Protocol freeze and preregistration

### Замораживаются

- exact claims;
- primary and secondary endpoints;
- smallest effect of interest;
- scenarios and split hashes;
- model IDs/hashes;
- prompts;
- JSON schemas;
- parser;
- compiler;
- Prolog modules;
- oracle;
- scorer;
- mode list;
- exclusion/retry policy;
- statistical scripts;
- table shells;
- stop/pivot rules.

### Preregistration artifact

Создаётся неизменяемый timestamped package с hash manifest.

В публичный репозиторий до submission можно положить hash и protocol without sealed data, если это не раскрывает double-blind identity strategy.

### Gate P12

Независимый internal reviewer может по package заранее воспроизвести план анализа, не видя outcomes.

---

## P13 — One-shot HOLDOUT execution

### Правила

- один запланированный execution window;
- все modes запускаются на frozen versions;
- outputs сохраняются до scoring;
- failed calls считаются incorrect, если failure policy не определяет infrastructure-wide invalidation;
- нельзя чинить отдельные responses;
- нельзя перезапускать только неудачные cases;
- любой полный rerun должен быть объявлен и включать все cases/modes;
- все unexpected events записываются до просмотра aggregate metrics.

### Firebreak

Лица, способные изменить system artifacts, не должны видеть case-level HOLDOUT errors до завершения locked analysis.

### Gate P13

- hash verification passed;
- raw outputs immutable;
- deviation log опубликован;
- primary result вычислен frozen script.

---

## P14 — Independent REPLICATION

### Отличие от HOLDOUT

Replication обязана менять хотя бы:

- source family;
- document templates;
- entity vocabulary;
- generator family;
- ideally execution operator/person.

### Нельзя

- исправлять system по HOLDOUT перед replication, если replication заявлена как подтверждение первоначального frozen effect;
- выбирать replication subset после просмотра результатов;
- использовать тот же generator prompt с другим seed как единственную независимость.

### Два допустимых маршрута

#### Confirmatory replication

Неизменная система применяется к новым sources.

#### Registered revised replication

Если HOLDOUT выявил инфраструктурный дефект, создаётся новая версия, но старый отрицательный результат сохраняется, а revised replication называется новым экспериментом.

### Gate P14

Direction of effect и practically meaningful magnitude подтверждены либо claim честно сужен.

---

## P15 — Confirmatory analysis and adversarial falsification

### Primary analysis

- exact contract accuracy;
- paired effect and confidence interval;
- hierarchical bootstrap;
- McNemar or prespecified paired test;
- comparison with strongest frozen baseline;
- result against smallest effect of interest.

### Secondary analysis

- by domain;
- by model size/family;
- by status;
- by query/extraction difficulty;
- latency/cost;
- teacher effects;
- frame ablations.

### Red-team questions

1. Можно ли объяснить effect тем, что frame содержит answer?
2. Можно ли объяснить effect меньшей длиной context?
3. Можно ли получить тот же результат deterministic template без LLM?
4. Использует ли student frame или повторяет priors?
5. Сохраняется ли effect без `allowedConclusion`?
6. Сохраняется ли effect на real messy sources?
7. Сохраняется ли effect при extracted query?
8. Независимы ли oracle и compiler?
9. Есть ли leakage между split families?
10. Исчезает ли effect на более сильных local models?
11. Не создаёт ли composite metric искусственное преимущество?
12. Не выбраны ли domains post-hoc?
13. Не скрыты ли malformed outputs?
14. Воспроизводимы ли closed-teacher results?
15. Интересен ли вывод, если student только копирует status?

### Обязательное правило

Для каждого abstract claim пишется strongest alternative explanation и control, который его исключает.

### Gate P15

Ни один primary claim не остаётся без adversarial control либо явного ограничения.

---

## P16 — Manuscript construction

### Main paper должен содержать

- один central question;
- один primary endpoint;
- одну основную causal figure;
- clear separation gold query / extracted query;
- error decomposition;
- matched controls;
- null and negative results;
- practical utility;
- limitations;
- broader impact при наличии privacy/security risks.

### Main-text priority

Критические данные нельзя прятать только в supplement, потому что reviewers могут его не читать.

В main PDF должны попасть:

- primary design;
- primary result;
- strongest baseline;
- core ablation;
- replication;
- main limitations;
- exact claim boundary.

### Claim language

Запрещены без прямого evidence:

- always;
- guarantees;
- solves hallucination;
- privacy-preserving;
- learns Prolog;
- formal correctness of source data;
- universal small-model improvement.

### Gate P16

Каждое предложение abstract имеет ссылку на figure/table/analysis row.

---

## P17 — Anonymous reproducibility artifact

### Критическая проблема

Основной LogicLens repository публично связан с автором и не может напрямую служить double-blind artifact, если ссылка раскрывает личность.

### Обязательный путь

Создать отдельный anonymous artifact snapshot:

- без Git history;
- без username/organization paths;
- без локальных путей `D:\projects\...`;
- без CGR user markers;
- без персональных metadata;
- без ссылок на именной GitHub;
- с neutral package name;
- с frozen hashes;
- с одной командой воспроизведения;
- с лицензиями и data manifest;
- размер supplement учитывает лимит TMLR;
- полный архив проверяется из clean environment.

### Public LogicLens

Остаётся development source of truth, но submission связывается только с anonymized snapshot в соответствии с double-blind policy.

После acceptance можно раскрыть canonical repository и связать history.

### Gate P17

Независимый человек не может определить авторство из artifact contents обычным просмотром файлов и metadata.

---

## P18 — TMLR submission readiness

### Текущие официальные требования, которые нужно перепроверить перед подачей

- anonymized double-blind manuscript;
- mandatory TMLR LaTeX style/template;
- complete active OpenReview profiles у всех authors;
- conflict information;
- appropriate Action Editor recommendations;
- originality and no parallel archival submission;
- supplementary materials anonymized;
- LLM use remains human-responsibility and must not create fabricated claims;
- broader impact statement при значимом риске harm;
- author submission quota checked;
- manuscript main-body length justified;
- artifact/supplement package within current size requirements.

Официальные страницы перед подачей:

- `https://jmlr.org/tmlr/acceptance-criteria.html`
- `https://jmlr.org/tmlr/author-guide.html`
- `https://jmlr.org/tmlr/editorial-policies.html`
- `https://jmlr.org/tmlr/ethics.html`
- `https://jmlr.org/tmlr/submissions.html`

### Desk-reject prevention

До подачи независимый reviewer отвечает:

1. работа явно в scope TMLR?
2. manuscript complete, а не roadmap?
3. основной результат виден без supplement?
4. claims narrow and supported?
5. anonymization clean?
6. related work current?
7. style/template untouched?
8. code/data statement честный?
9. ethics/privacy wording корректный?
10. нет archival overlap?

### Gate P18

Все ответы `yes`, submission package воспроизведён из clean checkout.

---

## P19 — Review, revision and resubmission path

### Во время TMLR review

- отвечать по claim/evidence matrix;
- не защищать лишние claims;
- при пробеле либо дать evidence, либо сузить claim;
- новые эксперименты регистрировать в deviation log;
- не менять primary endpoint;
- публиковать revised manuscript с clear change log.

### Если reject with invitation to resubmit

- сохранить public review history;
- построить issue list по каждому reviewer concern;
- провести только tests, закрывающие causal gaps;
- подать significantly revised manuscript с ссылкой на previous submission и change description согласно текущей policy.

### Если TMLR route исчерпан

Та же рукопись адаптируется без раздробления результата:

1. Journal of Web Semantics — усилить semantic representation, provenance и KG interoperability;
2. Knowledge-Based Systems — усилить knowledge-based decision-system framing;
3. SN Computer Science или другой широкий индексируемый venue — сохранить строгую empirical core.

### Запрещено

- одновременно подавать archival versions;
- скрывать предыдущий TMLR reject при resubmission туда же;
- создавать разные papers из одних и тех же results с существенным overlap.

---

# Часть II. Строгий аудит исходного контракта

## 5. Аудитная таблица

| № | Проблема | Severity | Почему опасно | Обязательное исправление |
|---:|---|---|---|---|
| A1 | `600 scenarios` без power analysis | Blocker | число выглядит произвольным | P4 simulation и SESOI |
| A2 | `M6-M3` меняет solver и interface одновременно | Blocker | результат могут назвать тривиальным | M9–M14 matched controls |
| A3 | Frame может содержать answer | Blocker | student только копирует | minimal/no-conclusion/template ablations |
| A4 | Shared compiler/oracle/scorer | Blocker | круговая корректность | independent implementation + mutations |
| A5 | Synthetic dominance | High | слабая внешняя валидность | real public messy sources |
| A6 | One closed teacher | High | невоспроизводимость | secondary claim, second teacher/human baseline |
| A7 | Account-default teacher identity | High | model drift | record resolved identity/config or weaken claim |
| A8 | Public named repo | Blocker | double-blind deanonymization | anonymous snapshot |
| A9 | Composite exact metric | High | скрывает механизм | component metrics + frozen hierarchy |
| A10 | Extraction dominates | High | formal effect не end-to-end | gold/extracted split and decomposition |
| A11 | DEV leakage through teacher logs | Blocker | adaptive overfitting | aggregate-only tooling enforcement |
| A12 | Replication generated by same templates | High | не независима | separate source/generator/operator |
| A13 | Multiple modes/metrics | High | researcher degrees of freedom | preregister primary contrast |
| A14 | Failed calls rerun selectively | High | bias | frozen retry policy |
| A15 | Model families all Qwen-like | Medium | weak generalization | independent architecture family |
| A16 | Hardware mismatch | Medium | impractical local claim | declared consumer profiles and measurements |
| A17 | Privacy wording too strong | High | unsupported guarantee | bounded-interface wording only |
| A18 | No publication operations path | Medium | avoidable desk reject | P17–P19 |
| A19 | No licensing audit | Medium | artifact cannot be published | source/license manifest |
| A20 | No human ambiguity handling | Medium | wrong gold labels | dual annotation/adjudication |
| A21 | No deterministic template baseline | High | LLM may be unnecessary | M11 |
| A22 | No corrupted-frame test | Medium | unclear whether model follows frame | M13 |
| A23 | No current related-work gate | Blocker | novelty overclaim | P1 before claim freeze |
| A24 | No canary leakage detection | High | hidden contamination | P8 canaries |
| A25 | Pilot cases reused conceptually | Medium | architecture overfit | new independent source/rule families |

Все Blocker issues должны быть закрыты до P12.

---

## 6. Самая сильная альтернативная интерпретация

Наиболее опасный reviewer critique:

> “The paper merely shows that executing a formal program with a formal solver is more accurate than asking a small language model to simulate the solver. The structured frame then exposes the answer, so the student contributes little.”

Статья выживает только если показывает одновременно:

1. solver result alone недостаточен или хуже typed interface (`M6 > M9`);
2. rich frame не сводится полностью к answer label (`M6` versus `M10/M12`);
3. LLM renderer добавляет измеримую ценность для объяснения или пользовательского контекста (`M6` versus `M11`), либо статья честно признаёт, что в части задач deterministic renderer лучше;
4. effect сохраняется при extracted query, а не только gold query;
5. эффект важен прежде всего для сохранения epistemic states и запрета unsupported conclusions;
6. результат переносится на unseen sources и model families.

Если пункты 1–3 не подтверждаются, центральный claim должен стать уже:

> **Small local LLMs should be restricted to interpretation and rendering around an externally verified decision contract rather than entrusted with formal execution.**

Это более узкий, но всё ещё публикуемый systems/behavioural result.

---

## 7. Проверка фальсифицируемости

Хорошая статья должна допускать результат, который её опровергает.

### H1 опровергнута, если

Strongest matched baseline не хуже M6 в replication с practically meaningful margin.

### H2 опровергнута, если

Effect существует только в одном domain/model либо исчезает на independent source family.

### H3 опровергнута, если

При gold frame renderer остаётся главным источником ошибок или formal runtime создаёт существенную долю ошибок.

### H4 не подтверждена, если

Teacher edits стабильно улучшают student при matched budgets и multiple runs.

### H5 сужается, если

Только `allowedConclusion` объясняет почти весь effect.

### H6 не подтверждена, если

Capsule program, построенная по S, не переносится на R-like public simulation без domain-specific ручной переделки.

Null results не удаляются. Они определяют новую допустимую формулировку.

---

## 8. Publication decision tree

```text
Does M6 beat strongest matched baseline on HOLDOUT?
 |
 +-- no --> Does rigorous failure analysis reveal generalizable boundary?
 |           |
 |           +-- yes --> submit failure/boundary study
 |           +-- no  --> stop flagship route, publish artifacts only
 |
 +-- yes --> Does effect replicate independently?
             |
             +-- no --> narrow to domain/model-specific result
             |
             +-- yes --> Is effect more than answer copying?
                         |
                         +-- no --> decision-contract paper
                         |
                         +-- yes --> full verified-interface paper
```

---

# Часть III. Операционный backlog

## 9. Полная последовательность deliverables

### Phase A — Research foundation

- [ ] P0 governance artifacts;
- [ ] P1 related-work matrix;
- [ ] P2 claim/evidence matrix;
- [ ] risk register;
- [ ] prohibited claims list.

### Phase B — Contracts and measurement

- [ ] unified publication case schema;
- [ ] query schema;
- [ ] decision-frame schema;
- [ ] score-record schema;
- [ ] semantic invariants;
- [ ] independent oracle design;
- [ ] exact metric hierarchy;
- [ ] power simulation.

### Phase C — Data

- [ ] D1 public sources;
- [ ] D2 public sources;
- [ ] D3 public sources;
- [ ] license manifest;
- [ ] source span index;
- [ ] scenario generator contracts;
- [ ] grouped split generator;
- [ ] leakage detector;
- [ ] canary mechanism;
- [ ] sealed HOLDOUT;
- [ ] separately sealed REPLICATION.

### Phase D — Modes and runtime

- [ ] M0–M8;
- [ ] M9 unstructured verified result;
- [ ] M10 minimal label;
- [ ] M11 deterministic renderer;
- [ ] M12 no-conclusion frame;
- [ ] M13 corrupted frame;
- [ ] M14 length-matched context;
- [ ] cold/warm runtime metrics;
- [ ] batch execution;
- [ ] proof/evidence trace;
- [ ] no-artifact checker.

### Phase E — Pilot and teachers

- [ ] DEV-only infrastructure pilot;
- [ ] floor/ceiling report;
- [ ] prompt teacher isolated track;
- [ ] program teacher isolated track;
- [ ] human baseline;
- [ ] second teacher when feasible;
- [ ] budget matching;
- [ ] teacher instability report.

### Phase F — Freeze and execution

- [ ] multi-model DEV matrix;
- [ ] final power confirmation;
- [ ] preregistration package;
- [ ] hash manifest;
- [ ] table shells;
- [ ] one-shot HOLDOUT;
- [ ] independent REPLICATION;
- [ ] frozen analysis.

### Phase G — Publication

- [ ] red-team report;
- [ ] manuscript;
- [ ] main-text evidence audit;
- [ ] anonymous artifact snapshot;
- [ ] clean-room reproduction;
- [ ] TMLR policy recheck;
- [ ] OpenReview profiles/quota/conflicts;
- [ ] submission;
- [ ] review response log;
- [ ] revision/resubmission route.

---

## 10. Definition of Done

Статья считается готовой к первой подаче только если одновременно:

1. central claim выдержал independent replication;
2. strongest alternative explanation проверено controls;
3. benchmark size обоснован power analysis;
4. primary comparison и endpoint preregistered;
5. compiler и oracle независимы;
6. real public messy sources представлены во всех трёх domains;
7. минимум четыре student profiles и две families завершены;
8. gold-query и extracted-query results разделены;
9. deterministic renderer baseline завершён;
10. frame-answer-copying critique закрыта или claim сужен;
11. все failed calls и exclusions опубликованы;
12. teacher results не являются единственной опорой central claim;
13. model weights/hashes и no-artifact contract проверены;
14. privacy claim ограничен фактически доказанным interface boundary;
15. anonymous artifact воспроизводится из clean environment;
16. manuscript соответствует текущим TMLR правилам;
17. каждое abstract sentence имеет отдельную evidence row;
18. adversarial internal reviewer не нашёл незакрытый Blocker;
19. submission package не раскрывает авторство;
20. существует заранее записанный маршрут при reject или null result.

Невыполнение хотя бы одного пункта 1–10 блокирует submission как flagship paper.

---

## 11. Что делать непосредственно после фиксации этого документа

Первый рабочий пакет должен закрыть фундамент, а не сразу расширять benchmark:

1. создать `claim-evidence-matrix.md`;
2. создать current related-work comparison matrix;
3. формализовать M9–M14 matched controls;
4. спроектировать independent oracle boundary;
5. написать power-analysis simulation plan;
6. определить anonymous artifact strategy;
7. только затем утверждать unified publication case schema.

Причина порядка: без claims, matched controls, independent oracle и power model можно построить большой, дорогой, но методологически непригодный benchmark.

---

## 12. Итоговая формула полного пути

```text
pilot observation
  -> novelty and causal question
  -> claim/evidence contract
  -> independent semantics and scoring
  -> powered leakage-safe benchmark
  -> matched controls
  -> DEV-only calibration
  -> preregistered freeze
  -> one-shot HOLDOUT
  -> independent replication
  -> adversarial falsification
  -> anonymous reproducible artifact
  -> TMLR submission
  -> evidence-driven revision or venue adaptation
```

Главный принцип:

> **Сначала устранить все альтернативные объяснения эффекта, затем масштабировать эксперимент. Не наоборот.**
