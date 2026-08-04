# Научные развилки после verified capsule query

Дата фиксации: 2026-08-04  
Статус: исследовательская карта решений  
Проект: LogicLens / EpistemicCompilerLab

## 1. Отправная точка

К началу этой карты уже существует воспроизводимый строгий контур:

- JSONL assertions проходят schema validation;
- knowledge capsule канонизируется и получает package hash;
- JSON-запрос проверяется по схеме, predicate space, arity и semantic IDs;
- `capsule_query.py` выполняет запрос через SWI-Prolog;
- результат независимо сверяется с packaged JSONL;
- наружу возвращается deterministic decision frame с `status`, `action`, provenance, scope, dependency groups и warnings.

Локальный CGR-прогон `20260804-224325` подтвердил четыре базовых состояния на реальной management-капсуле:

| Запрос | Ожидаемое состояние | Получено |
|---|---|---|
| Product Owner владеет product value в Scrum 2020 | `supported` | `supported` |
| Team Lead владеет people performance management в модели GitLab | `refuted` | `refuted` |
| Product Manager владеет Product Backlog management | `unknown` | `unknown` |
| Synthetic hybrid lead владеет technical direction при противоположных источниках | `conflicting` | `conflicting` |

Package hash:

```text
sha256:7a8b529a9acde057ee667a3b3862e1db1006cc278959e92d213a25d337ea8e70
```

Это важный переход. Научный вопрос теперь не в том, можно ли технически вызвать Prolog из LLM-процесса, а в том, **какая дополнительная семантика окупается, в каких задачах и при каком способе взаимодействия с моделью**.

Связанные документы:

- [`../research/SELECTIVE_EPISTEMIC_TOOL_USE.md`](../research/SELECTIVE_EPISTEMIC_TOOL_USE.md)
- [`../../docs/architecture/EPISTEMIC_DSL_V0.md`](../../docs/architecture/EPISTEMIC_DSL_V0.md)
- [`../research/TEACHER_STUDENT_EXPERIMENT.md`](../research/TEACHER_STUDENT_EXPERIMENT.md)
- [`../../docs/architecture/CAPSULE_QUERY_V0.md`](../../docs/architecture/CAPSULE_QUERY_V0.md)

---

## 2. Центральная рекомендация

Не следует превращать ближайшую работу в один слишком широкий проект «реализовать почти весь DSL и проверить, стало ли лучше». Такая постановка смешает сразу несколько причин результата:

- модель получила новые факты;
- модель получила формальный вывод;
- модель получила численную неопределённость;
- изменился формат представления;
- появился router;
- изменился объём prompt;
- улучшился extractor;
- появилась новая decision policy.

Сильнее строить программу как **последовательность замороженных семантических ступеней**. На каждой ступени меняется один основной слой DSL, а остальной pipeline и benchmark сохраняются.

Рекомендуемая последовательность:

```text
S0  Direct Codex, без capsule
S1  Strict claims: support / oppose / unknown / conflict
S2  Strict logical rules + proof DAG
S3  Typed observations + units + bounds
S4  Binomial opinions: belief / disbelief / uncertainty / base rate
S5  Versioned decision policies
S6  Fuzzy membership
S7  Calibrated assessments + posterior / credible / credal products
```

Параллельно, но как отдельная ось:

```text
M0  Direct
M1  Full context
M2  Always query
M3  Self-routed
M4  Learned/rule router
M5  Hybrid material-formal
M6  Oracle routing
```

Полный декартов продукт `S × M` слишком дорог и плохо интерпретируем. Нужен staged design:

1. семантические ступени сравниваются сначала в фиксированных режимах `Always query` и `Hybrid`;
2. лучший или минимально достаточный DSL слой затем используется в routing-эксперименте;
3. формат четырёх чисел исследуется отдельным representation study;
4. оценка всего ответа исследуется отдельно от оценки атомарных claims.

---

## 3. Развилка A — progressive DSL как главная статья

### Научная гипотеза

Каждый новый формальный слой должен давать измеримый прирост только на тех семействах задач, для которых его семантика необходима. Если слой улучшает средний результат только потому, что вместе с ним в prompt попало больше правильного текста, это не доказательство полезности DSL.

### Эксперимент

Для каждой ступени `S1–S7` должны существовать:

- задачи, где новый слой необходим;
- задачи, где предыдущего слоя достаточно;
- задачи, где новый слой нерелевантен;
- adversarial controls, провоцирующие неправильное использование нового типа данных.

Пример для `S4 opinions`:

- одинаковая projected probability, но разная uncertainty;
- одинаковые `b,d,u`, но разные base rates;
- одинаковая expected probability, но разный conflict;
- высокий belief при низком coverage;
- сильный prior при слабых evidence;
- конфликтующие dependency groups;
- два почти одинаковых source records, которые нельзя считать независимыми.

### Сильный результат

Не «S4 точнее S3 в среднем», а более конкретный вывод:

> Добавление binomial opinions почти не меняет обычную factual accuracy, но существенно снижает unsupported certainty и улучшает различение evidence-backed belief, ignorance и prior-driven projection.

### Отрицательный, но ценный результат

Если Codex одинаково трактует разные `b,d,u,a` и сворачивает их в один scalar, это важный результат о границе полезности raw uncertainty representation.

### Риск

Слишком много ступеней размоет статистическую мощность и породит множество вторичных сравнений.

### Решение

Для первой основной статьи ограничиться:

```text
S1 strict claims
S2 logical rules
S3 typed observations
S4 binomial opinions
```

`S5–S7` оставить как последующее расширение, если error analysis показывает необходимость.

---

## 4. Развилка B — selective routing как главная статья

### Научная гипотеза

Verified capsule полезна не всегда. Система должна научиться различать:

- вопрос можно надёжно решить параметрически;
- вопрос требует capsule;
- вопрос требует сначала material interpretation, затем formal query;
- capsule не содержит нужной семантики и должна вернуть `unknown`;
- tool недоступен или package не соответствует requested version.

### Почему это сильная линия

Она исследует не только reasoning accuracy, но и **необходимость, полезность и стоимость вызова**. Это даёт practically relevant Pareto frontier:

```text
качество ↑
unsupported certainty ↓
latency ↓
tokens ↓
tool calls ↓
```

### Критические контрольные режимы

- `Direct`: никакой capsule;
- `Full context`: evidence передано в prompt, но formal runtime отсутствует;
- `Always query`: tool вызывается всегда;
- `Self-routed`: решение принимает Codex;
- `Rule router`: решение по явно объявленным признакам;
- `Oracle`: лучший путь выбирается по известному outcome;
- `Hybrid`: Codex формализует атомарные claims, DSL их проверяет.

### Главный риск

Router может учиться не epistemic necessity, а поверхностным шаблонам benchmark.

### Защита

Split должен выполняться по:

- source families;
- rule templates;
- predicate families;
- document versions;
- entity families;
- paraphrase generators.

Нельзя ограничиваться случайным разделением близких перефразировок.

### Критерий успеха

Deployable router должен приближаться к oracle frontier и одновременно:

- сохранять большую часть quality gain `Always query`;
- избегать значимой доли ненужных вызовов;
- не ухудшать necessary-tool recall;
- не маскировать `unknown` прямым уверенным ответом.

### Рекомендация

Selective routing оставить центральной системной гипотезой, а progressive DSL использовать как controlled treatment внутри неё. Рабочее название:

> Progressive Selective Epistemic Tool Use: When Richer Verified Semantics Justify Their Cost

---

## 5. Развилка C — как Codex понимает четыре числа `b,d,u,a`

### Объект исследования

Binomial opinion:

```text
ω = (b, d, u, a)

b + d + u = 1
P = b + a × u
```

где:

- `b` — belief mass;
- `d` — disbelief mass;
- `u` — uncommitted uncertainty;
- `a` — base rate;
- `P` — projected probability.

Это не четыре взаимозаменяемые вероятности.

### Главное исследовательское различие

Нужно разделить:

1. **математическую корректность kernel**;
2. **семантическое понимание frame моделью**;
3. **правильное действие на основании frame**;
4. **корректное объяснение пользователю**.

Codex может верно прочитать числа, но сделать неверную рекомендацию. Может выбрать верное действие, но объяснить `u` как «вероятность ошибки». Может использовать `P`, проигнорировав, что projection в основном определяется base rate.

### Representation conditions

#### R0 — scalar only

```json
{"probability": 0.74}
```

#### R1 — raw tuple

```json
{"b": 0.62, "d": 0.08, "u": 0.30, "a": 0.40}
```

#### R2 — named tuple

```json
{
  "belief": 0.62,
  "disbelief": 0.08,
  "uncertainty": 0.30,
  "baseRate": 0.40
}
```

#### R3 — computed frame

```json
{
  "belief": 0.62,
  "disbelief": 0.08,
  "uncertainty": 0.30,
  "baseRate": 0.40,
  "projectedProbability": 0.74,
  "allowedConclusion": "moderately_supported",
  "warnings": [
    "substantial_uncertainty",
    "base_rate_materially_affects_projection"
  ]
}
```

#### R4 — computed frame + evidence trace

Добавляются dependency groups, source scope, fusion policy и proof/evidence DAG.

### Контрастные пары

Нужны paired cases, где один scalar совпадает, а эпистемический профиль различается:

| Пара | Одинаково | Отличается | Ожидаемое различие ответа |
|---|---|---|---|
| A | `P` | `u` | разная степень осторожности |
| B | `b,d,u` | `a` | объяснить роль prior |
| C | `P` | conflict index | сообщить о конфликте |
| D | `b` | coverage | не выдавать частично проверенный ответ за полный |
| E | evidence count | dependency structure | не переоценивать дубликаты |

### Метрики

- tuple interpretation accuracy;
- projected probability use accuracy;
- base-rate misuse rate;
- uncertainty-collapse rate;
- conflict-collapse rate;
- allowed-conclusion compliance;
- explanation faithfulness;
- decision accuracy;
- user-facing overstatement rate.

### Возможный сильный результат

> Raw tuple не помогает или даже ухудшает ответы, тогда как verified interpreted frame повышает epistemic faithfulness. Следовательно, LLM не следует поручать самостоятельную эпистемическую арифметику и семантическую интерпретацию чисел.

### Возможный отрицательный результат

Если `R3/R4` почти не превосходит scalar при сильном Codex, это ограничивает ценность rich frame для сильных моделей, но может сохранить ценность для слабых локальных моделей и аудита.

---

## 6. Развилка D — четыре числа для всего ответа

### Главная опасность

Нельзя просто усреднить opinions отдельных предложений и назвать результат «вероятностью истинности ответа».

Ответ содержит разные типы элементов:

- factual claims;
- assumptions;
- derived claims;
- recommendations;
- value judgements;
- decision trade-offs;
- procedural completeness;
- неизвестные или неформализованные части.

### Допустимая формализация

Сначала объявляется конкретная proposition, например:

```text
answer_satisfies_contract(answer_id, rubric_version)
```

или:

```text
answer_core_claims_supported(answer_id, capsule_version)
```

Затем фиксируются:

- claim extraction policy;
- mandatory claims;
- weights или fusion semantics;
- dependency model;
- treatment unknown/conflict;
- coverage definition;
- aggregation version.

Результат должен включать отдельные продукты:

```json
{
  "answerOpinion": {
    "belief": 0.48,
    "disbelief": 0.27,
    "uncertainty": 0.25,
    "baseRate": 0.50,
    "projectedProbability": 0.605
  },
  "conflictIndex": 0.18,
  "formalizedCoverage": 0.82,
  "rubricScore": 76,
  "mandatoryFailureCount": 1
}
```

Эти значения нельзя сворачивать в один score:

- opinion относится к объявленной proposition;
- coverage показывает долю формализованного содержания;
- rubric score оценивает выполнение задания;
- mandatory failures могут блокировать pass независимо от среднего score;
- conflict показывает несовместимость evidence;
- практическая decision quality может требовать экспертной или outcome-based оценки.

### Научные подветки

#### D1 — conservative aggregation

Итог ограничивается наиболее слабым mandatory claim.

Плюс: безопасно.  
Минус: один локальный дефект может обнулить сильный ответ.

#### D2 — evidence fusion

Claims переводятся в evidence и агрегируются с dependency-aware fusion.

Плюс: соответствует общей эпистемической модели.  
Минус: нужен обоснованный mapping claim outcomes → evidence weights.

#### D3 — rubric proposition

Opinion строится не о «правдивости текста», а о выполнении версии rubric.

Плюс: практически понятнее.  
Минус: часть критериев качественная и не является world fact.

#### D4 — multi-profile output

Система вообще не создаёт один итоговый opinion, а показывает несколько профилей:

```text
factual support
scope compliance
evidence coverage
decision completeness
risk handling
```

Плюс: честнее и информативнее.  
Минус: пользователю сложнее воспринимать.

### Рекомендация

Для первой статьи не объявлять «четыре числа правильности всего ответа». Исследовать сначала:

1. opinions атомарных claims;
2. claim coverage;
3. отдельный deterministic rubric score;
4. пользовательское восприятие multi-profile display.

Answer-level opinion вынести в отдельную работу после появления эмпирически обоснованной aggregation policy.

---

## 7. Развилка E — gold query против LLM extraction

### Почему это критично

End-to-end ошибка может возникнуть в разных местах:

```text
текст пользователя
→ semantic parsing
→ entity linking
→ predicate selection
→ query construction
→ formal execution
→ frame interpretation
→ final rendering
```

Если измерять только конечный ответ, нельзя понять, улучшился ли DSL или extractor.

### Обязательные режимы

#### E0 — gold formal query

Natural language parsing исключён. Проверяется только runtime и использование frame.

#### E1 — constrained extractor

LLM выбирает только из объявленных predicates и semantic IDs по JSON Schema.

#### E2 — free extractor

LLM самостоятельно предлагает formalization, затем validator может её отклонить.

#### E3 — clarification-aware extractor

При неоднозначности модель должна не угадывать, а сформировать clarification request.

### Метрики

- predicate accuracy;
- argument linking accuracy;
- arity validity;
- semantic-ID validity;
- query exact match;
- acceptable alternative formalization rate;
- rejected-query recovery rate;
- clarification precision/recall;
- runtime correctness conditioned on correct query.

### Сильный возможный вывод

> После правильной formalization DSL почти безошибочен; большая часть residual error находится на natural-to-formal boundary.

Это создаёт отдельную научную ценность: verified runtime делает ошибки локализуемыми и исправляемыми.

---

## 8. Развилка F — dependency-aware fusion

### Научная проблема

Количество evidence records не равно количеству независимых свидетельств.

Типичные зависимости:

- две статьи пересказывают один источник;
- несколько полей взяты из одной модели;
- результаты используют общий dataset;
- два эксперта согласовали позицию совместно;
- несколько claims выведены из одной исходной premise;
- один документ существует в нескольких версиях или копиях.

Если зависимость игнорировать, belief может искусственно расти. Современная neuro-symbolic литература отдельно указывает на опасность independence assumptions и reasoning shortcuts.

### Возможные модели

#### F1 — dependency groups

Текущий минимальный подход: внутри группы evidence не считается независимым.

#### F2 — dependency DAG

Records могут иметь частичное происхождение и общие ancestors.

#### F3 — correlation bounds

Вместо одного fusion result возвращается диапазон допустимых результатов при нескольких dependency assumptions.

#### F4 — explicit fusion profiles

Например:

```text
conservative
clustered
independent-only
sensitivity-analysis
```

### Научный эксперимент

Создать cases с одинаковыми текстами evidence, но разной dependency structure. Проверять:

- меняется ли kernel result корректно;
- понимает ли Codex причину различия;
- не пересчитывает ли модель дубликаты как независимые;
- сообщает ли sensitivity к assumption.

### Рекомендация

Dependency-aware fusion должна войти в opinion layer до любых серьёзных claims о калибровке. Иначе четыре числа могут быть математически корректны для неверной модели независимости.

---

## 9. Развилка G — typed observations и численная семантика

### Зачем этот слой нужен

Strict status не покрывает задачи, где вопрос относится к:

- измерению;
- диапазону;
- единицам;
- доверительному или credible интервалу;
- threshold policy;
- сравнению нескольких revisions;
- propagation uncertainty.

### Минимальный publication-grade subset

```text
point
bounded
normal
unit
conversion allowlist
observation provenance
dependency group
```

### Контрольные задачи

- неверная единица при правильном числе;
- overlapping bounds;
- threshold внутри uncertainty interval;
- point estimate выше порога, lower bound ниже;
- две revisions с разными units;
- normal distribution против bounded interval;
- missing conversion rule;
- contradictory measurements from dependent sources.

### Главный риск

Статья может превратиться в описание numerical library.

### Решение

Добавлять kernel только вместе с вопросом поведения LLM:

> Улучшает ли typed verified numerical frame принятие решений по сравнению с raw numbers или prose evidence?

---

## 10. Развилка H — fuzzy membership

### Когда fuzzy действительно оправдана

Fuzzy membership полезна, если термин по природе постепенный:

- «высокая доступность»;
- «критический риск»;
- «Earth-sized»;
- «достаточно зрелый процесс».

Она не должна использоваться для маскировки отсутствующего точного predicate или неопределённой истины.

### Возможные ошибочные смешения

Codex может принять membership за:

- probability of truth;
- model confidence;
- population frequency;
- evidence strength;
- expected utility.

### Научный вопрос

Сможет ли verified frame сохранить различие между:

```text
вероятность, что объект имеет свойство
степень соответствия объекта размытому понятию
неопределённость измерения входного значения
```

### Рекомендация

Не реализовывать fuzzy до первого observation experiment. Он нужен только если benchmark действительно содержит полезные vague predicates, а не ради полноты языка.

---

## 11. Развилка I — calibrated assessments, credible и credal uncertainty

### Почему это самый рискованный слой

Classifier score нельзя автоматически трактовать как probability of truth. Даже после calibration остаются:

- dataset shift;
- model misspecification;
- calibration uncertainty;
- dependency between models;
- prior sensitivity;
- distinction aleatoric/epistemic;
- distinction credible interval/credal bounds.

### Минимальные требования до реализации

- named calibration adapters;
- immutable calibration dataset hashes;
- out-of-domain tests;
- independent numerical oracle;
- sensitivity analysis;
- separation conflict and uncertainty;
- explicit model/version scope;
- no arithmetic delegated to LLM.

### Возможная статья

Этот слой способен стать отдельной работой:

> Verified Probabilistic Epistemic Frames for Language-Model Decision Support

Не следует делать его обязательным условием первой публикации LogicLens.

---

## 12. Развилка J — human-facing epistemic profile

### Исследовательский вопрос

Пользовательская визуализация может улучшить понимание, а может создать ложную точность.

Нужно сравнить представления:

- одна probability;
- четыре числа;
- четыре числа + natural-language labels;
- verified conclusion + warnings;
- evidence breakdown;
- multi-profile answer view;
- qualitative bands без процентов.

### Пользовательские метрики

- правильное понимание uncertainty;
- правильное понимание base rate;
- различение ignorance и conflict;
- decision quality;
- trust calibration;
- willingness to seek more evidence;
- false precision perception;
- time to decision.

### Риск

HCI-эксперимент требует людей, согласия, дизайна анкеты и отдельной статистики. Он замедлит systems paper.

### Рекомендация

Сначала исследовать Codex-as-consumer. Human-facing profile вынести в отдельную HCI/decision-support линию после стабилизации semantics.

---

## 13. Развилка K — efficiency и runtime architecture

### Почему производительность научно важна

Если каждый atomic claim запускает новый SWI-Prolog process и повторно проверяет package, `Always query` заведомо будет дорогим. Тогда routing result будет частично измерять не семантическую необходимость, а неоптимальную реализацию.

### Нужные режимы

- cold package verification;
- warm verified package cache;
- one query per process;
- batch query;
- persistent isolated worker;
- local package versus remote tool;
- raw JSONL calculation versus SWI-Prolog cross-check;
- proof DAG on/off.

### Минимальная следующая оптимизация

`batch-strict-claim`:

```json
{
  "schemaVersion": "0.1",
  "operation": "batch-strict-claim",
  "queries": [
    {"id": "q1", "target": {...}},
    {"id": "q2", "target": {...}}
  ]
}
```

Package verification выполняется один раз, SWI-Prolog process — один раз, результаты остаются individually hashed.

### Критерий

Routing study должен публиковать и cold, и warm latency. Иначе вывод о стоимости tool use будет зависеть от случайной deployment architecture.

---

## 14. Развилка L — предметные области и внешняя валидность

### Минимум три структуры знаний

#### L1 — management/software governance

- open-world claims;
- role scopes;
- versioned frameworks;
- local policies;
- conflicts.

#### L2 — engineering specifications

- revisions;
- typed measurements;
- ranges;
- units;
- exceptions;
- exact source fields.

#### L3 — scientific/technical classification

- assessments;
- uncertainty;
- fuzzy concepts;
- conflicting sources;
- dependency-aware fusion.

### Почему management недостаточно

На management domain можно показать scope, conflict и open-world semantics, но сложно обосновать numerical kernels, calibration и fuzzy membership.

### Почему полностью synthetic data недостаточно

Synthetic/private facts полезны для исключения model-memory leakage, но могут не отражать real-world ambiguity и source defects.

### Рекомендуемый баланс

- procedurally generated private domain для non-guessable truth;
- versioned public documents для reproducibility;
- real engineering documents для messy source structure;
- synthetic controls для exact causal isolation.

---

## 15. Как не перегрузить одну статью

### Вариант P1 — одна широкая systems paper

Содержит routing, progressive DSL, opinions, answer aggregation и UI.

Проблема: слишком много независимых вкладов, слабая причинная интерпретация, огромный benchmark и множество сравнений.

### Вариант P2 — рекомендуемый портфель

#### Paper A — основной

**Progressive Selective Epistemic Tool Use**

Вклад:

- strict claims;
- logical rules;
- typed observations;
- selective routing;
- gold versus extracted queries;
- cost/quality frontier.

#### Paper B — uncertainty representation

**Do Language Models Understand Four-Component Epistemic Opinions?**

Вклад:

- `b,d,u,a` representation study;
- same-projection contrast pairs;
- conflict and dependency controls;
- raw tuple versus interpreted frame;
- strong and weak model comparison.

#### Paper C — answer-level profiles

**From Verified Claims to Epistemic Profiles of Long-Form Answers**

Вклад:

- claim extraction with quote binding;
- coverage;
- aggregation policies;
- rubric separation;
- human-facing explanations.

### Преимущество P2

Каждая статья имеет один главный причинный вопрос и может получить самостоятельный отрицательный результат.

---

## 16. Приоритеты по научной ценности

| Приоритет | Ветка | Научная ценность | Инженерная стоимость | Главный риск |
|---:|---|---:|---:|---|
| 1 | Gold/extracted query decomposition | очень высокая | средняя | evaluator ambiguity |
| 2 | Logical rules + proof DAG | высокая | средняя | rule language scope |
| 3 | Selective routing | очень высокая | средняя | benchmark leakage |
| 4 | Four-number representation study | очень высокая | средняя | числа не влияют на сильный Codex |
| 5 | Typed observations | высокая | средняя | numerical-library drift |
| 6 | Dependency-aware fusion | высокая | высокая | трудно задать ground truth dependency |
| 7 | Batch/warm runtime | необходимая инфраструктура | низкая–средняя | мало самостоятельной новизны |
| 8 | Answer-level opinion | высокая, но поздняя | высокая | misleading scalar |
| 9 | Fuzzy membership | условная | средняя | путаница membership/probability |
| 10 | Full calibrated uncertainty | потенциально очень высокая | очень высокая | numerical validity |
| 11 | Human-facing profile | высокая для HCI | высокая | нужны участники |
| 12 | «Почти полный DSL» сам по себе | низкая как научная claim | очень высокая | engineering-only contribution |

---

## 17. Рекомендуемая программа ближайших milestone

### Milestone 1 — causal baseline

1. Добавить benchmark-case schema.
2. Зафиксировать `Direct`, `Full context`, `Always query`, `Hybrid`.
3. Разделить gold query и extracted query.
4. Создать 90-case engineering benchmark:
   - 30 direct-favoured;
   - 30 capsule-favoured;
   - 30 hybrid-favoured.
5. Публиковать полный error taxonomy.

### Milestone 2 — logical layer

1. Реализовать safe `logical_rule`.
2. Добавить cycle/unsafe-variable rejection.
3. Возвращать proof DAG.
4. Создать multi-hop cases и matched single-hop controls.
5. Повторить frozen experiment.

### Milestone 3 — runtime fairness

1. Добавить batch query.
2. Измерить cold/warm latency.
3. Зафиксировать package cache policy.
4. Повторить routing analysis.

### Milestone 4 — typed observations

1. Реализовать `point`, `bounded`, `normal`.
2. Добавить unit allowlist.
3. Добавить deterministic kernels и oracle tests.
4. Создать numerical decision cases.
5. Сравнить raw numbers, full context и verified numerical frame.

### Milestone 5 — opinions

1. Реализовать opinion kernel с `b,d,u,a`.
2. Добавить dependency-aware evidence grouping.
3. Вывести projected probability отдельно.
4. Сохранить conflict отдельным продуктом.
5. Создать contrast-pair benchmark.
6. Сравнить `R0–R4` представления.

### Milestone 6 — model selection

По результатам предыдущих стадий решить:

- нужен ли fuzzy layer;
- нужен ли calibrated assessment layer;
- достаточно ли rule router;
- оправдана ли отдельная answer-level paper;
- какие domains нужны для replication.

---

## 18. Критерии остановки и смены направления

### Остановить расширение logical DSL, если

- gold-query strict runtime уже решает почти все formal cases;
- multi-hop tasks не дают отдельного преимущества над full-context Codex;
- proof DAG не повышает faithfulness или auditability.

### Отложить opinions, если

- benchmark не содержит задач с различимыми evidence/ignorance/prior states;
- projected scalar решает все реальные decisions;
- dependency ground truth невозможно защитить.

### Не добавлять fuzzy, если

- vague categories можно лучше представить explicit bounded policy;
- membership не меняет решение;
- пользователи или модели систематически принимают membership за probability.

### Не строить answer-level opinion, если

- claim extraction coverage нестабильна;
- aggregation policy сильно меняет итог;
- один scalar скрывает mandatory failures;
- multi-profile display оказывается честнее.

### Сменить central claim, если

- `Full context` стабильно равен verified query по качеству;
- formal runtime не снижает hallucination/overstatement;
- routing headroom близок к нулю;
- latency полностью доминирует utility даже в warm/batch режиме.

В этом случае научная ценность может сместиться к:

- auditability;
- reproducibility;
- provenance preservation;
- fail-closed behaviour;
- formal error localization.

---

## 19. Предрегистрируемые основные гипотезы

### H1 — progressive necessity

Новый DSL layer улучшает результаты преимущественно на cases, для которых его семантика необходима, и не должен автоматически улучшать matched controls.

### H2 — frame over tuple

Computed verified opinion frame превосходит raw `b,d,u,a` по правильности интерпретации и allowed-conclusion compliance.

### H3 — same probability is not same epistemic state

Codex без rich frame чаще выдаёт одинаковые объяснения для cases с одинаковой projected probability, но различными uncertainty, prior или conflict.

### H4 — extraction dominates residual error

При gold formal queries большая часть runtime errors исчезает; residual end-to-end errors концентрируются в natural-to-formal translation.

### H5 — selective frontier

Router приближается к oracle quality-cost frontier и превосходит both Direct и Always-query на смешанном benchmark.

### H6 — dependency matters

Игнорирование dependency structure систематически завышает strength of support и ухудшает calibrated decision behaviour.

### H7 — no single answer number

Multi-profile answer evaluation лучше сохраняет mandatory failures, unknown и coverage, чем один агрегированный projected probability.

---

## 20. Статистический и репликационный минимум

- одинаковые cases для paired comparisons;
- bootstrap confidence intervals;
- McNemar test для paired correctness;
- paired latency comparisons;
- correction for multiple secondary comparisons;
- несколько независимых запусков stochastic model conditions;
- frozen model IDs, prompts, schemas, source hashes и runtime versions;
- HOLDOUT не используется для выбора layer/router;
- REPLICATION использует другие sources и templates;
- все rejected queries и tool failures публикуются;
- исключения cases допускаются только по заранее объявленным причинам.

Для вероятностных outputs proper scoring rules допустимы только там, где ground truth действительно вероятностный или построен на repeated outcomes. Нельзя заявлять calibration четырёх чисел только по deterministic factual labels.

---

## 21. Наиболее сильная итоговая траектория

Рекомендуемая научная программа:

```text
verified strict runtime
→ gold/extracted boundary experiment
→ logical proof layer
→ selective routing baseline
→ typed observations
→ four-number opinion representation study
→ dependency-aware fusion
→ answer-level multi-profile research
→ fuzzy/calibrated layers только по результатам error analysis
```

Главная идея проекта при этом остаётся ясной:

> LogicLens не пытается заменить языковое рассуждение формальным решателем. Он выделяет те части ответа, где поддержка, опровержение, незнание, конфликт, численная неопределённость, scope и provenance должны вычисляться проверяемо, и исследует, когда стоимость такого вычисления оправдана.

---

## 22. Литературный контекст

Ниже перечислены работы, полезные для positioning. Они не заменяют собственный benchmark и не доказывают заявленные гипотезы LogicLens.

1. Allen et al. **Sound and Complete Neurosymbolic Reasoning with LLM-Grounded Interpretations**. NeSy 2025.  
   https://proceedings.mlr.press/v284/allen25a.html

2. van Krieken et al. **Neurosymbolic Reasoning Shortcuts under the Independence Assumption**. NeSy 2025.  
   https://proceedings.mlr.press/v284/krieken25a.html

3. Chen. **A Comparative Study of Neurosymbolic AI Approaches to Interpretable Logical Reasoning**. NeSy 2025.  
   https://proceedings.mlr.press/v284/chen25b.html

4. Bagheri Nezhad and Agrawal. **Enhancing Large Language Models with Neurosymbolic Reasoning for Multilingual Tasks**. NeSy 2025.  
   https://proceedings.mlr.press/v284/nezhad25a.html

5. Quan et al. **PEIRCE: Unifying Material and Formal Reasoning via LLM-Driven Neuro-Symbolic Refinement**. ACL 2025 Demo.  
   https://aclanthology.org/2025.acl-demo.2/

6. Yang et al. **Neuro-Symbolic Artificial Intelligence: Towards Improving the Reasoning Abilities of Large Language Models**. IJCAI 2025 Survey.  
   https://www.ijcai.org/proceedings/2025/1195

7. Song et al. **IRT-Router: Effective and Interpretable Multi-LLM Routing via Item Response Theory**. ACL 2025.  
   https://aclanthology.org/2025.acl-long.761/

8. Huang et al. **RouterEval: A Comprehensive Benchmark for Routing LLMs**. EMNLP Findings 2025.  
   https://aclanthology.org/2025.findings-emnlp.208/

9. Manginas et al. **A Scalable Approach to Probabilistic Neuro-Symbolic Robustness Verification**. NeSy 2025.  
   https://proceedings.mlr.press/v284/manginas25a.html

10. Ledaguenel et al. **A Complexity Map of Probabilistic Reasoning for Neurosymbolic Classification Techniques**. Mathematics in Computer Science, 2025.  
    https://link.springer.com/article/10.1007/s11786-025-00603-7

11. Jøsang. **Subjective Logic: A Formalism for Reasoning Under Uncertainty**. Springer, 2016.

---

## 23. Следующее решение

Перед реализацией нового DSL layer нужно принять одно архитектурно-научное решение:

> Основной ближайший эксперимент строится вокруг `logical_rule + proof DAG`, либо сначала вокруг benchmark/extractor/router на уже готовом strict layer?

Рекомендуемый выбор:

1. сначала benchmark schema и gold/extracted split;
2. затем logical rule layer;
3. затем первый progressive experiment;
4. только после этого opinion kernel.

Так мы не создадим сложную математику до появления evaluator, способного честно показать её marginal value.
