# Нарастающие версии Epistemic DSL на курсе руководителей

Дата фиксации: 2026-08-04  
Статус: исполняемый исследовательский план  
Контур: LogicLens / EpistemicCompilerLab / CTO Practical Simulation

## 1. Цель

Построить несколько совместимых уровней Epistemic DSL и после добавления каждого уровня повторять один и тот же замороженный набор управленческих задач.

Исследовательский вопрос:

> Как добавление новых формальных эпистемических возможностей меняет точность, сохранение неизвестности и конфликта, объяснимость, стоимость и поведение Codex на задачах курса руководителей?

Нельзя одновременно менять DSL, вопросы, источники и scoring. Для причинного сравнения фиксируются:

- тексты кейсов;
- gold decomposition;
- rubric;
- источники и их хеши;
- prompt и response schema;
- модель и параметры запуска;
- метрики и stopping rules.

Меняется только `dslLevel` и доступный этому уровню verified frame.

## 2. Версии

### DSL-A — strict open-world claims

Уже реализованный базовый уровень:

- typed predicates и semantic IDs;
- explicit `support` и `oppose`;
- provenance;
- dependency groups;
- scope и generalisability;
- `supported`, `refuted`, `unknown`, `conflicting`;
- package/query hashes;
- Python–SWI-Prolog cross-verification.

Применение в курсе:

- границы ролей;
- различие Product Owner и Product Manager;
- явное опровержение ошибочного присвоения ответственности;
- сохранение `unknown` при отсутствии данных.

### DSL-B — strict logical derivation

Добавляются безопасные правила над DSL-A:

- `all`;
- `any`;
- `exists` только над объявленным конечным semantic domain;
- `not_explicit` как явно маркированная open-world проверка отсутствия конкретной стороны свидетельства;
- cycle rejection;
- safe-variable validation;
- proof DAG;
- derived evidence, не смешиваемое с source assertion.

Применение в курсе:

- если CTO владеет технологической стратегией и обнаружен материальный технологический риск, то CTO обязан подготовить эскалацию владельцу бизнес-риска;
- если решение требует нескольких обязательных owners, отсутствие хотя бы одного не позволяет считать decision package полным;
- вывод о необходимости эскалации строится из нескольких premises, а не хранится готовым assertion.

### DSL-C — typed observations

Добавляются:

- `point`;
- `bounded`;
- `normal`;
- units и allowlisted conversions;
- observation provenance;
- dependency groups;
- deterministic numerical kernels;
- comparison policies над точками и границами.

Применение в курсе:

- текущая и целевая доступность;
- число инцидентов;
- доля автотестов;
- бюджет и резерв;
- срок до запуска;
- диапазон capacity команды.

DSL-C должен различать:

- точное значение;
- оценку с диапазоном;
- распределение;
- отсутствие измерения;
- несовместимые единицы.

### DSL-D — binomial opinions

Добавляется мнение Subjective Logic:

- `belief`;
- `disbelief`;
- `uncertainty`;
- `baseRate`;
- `projectedProbability = belief + baseRate × uncertainty`;
- отдельный `conflictIndex`;
- dependency-aware fusion;
- запрет LLM самостоятельно выполнять эпистемическую арифметику.

Инвариант:

```text
belief + disbelief + uncertainty = 1
```

Применение в курсе:

- насколько подтверждено, что запуск пройдёт без критического инцидента;
- насколько подтверждена достаточность mitigation plan;
- насколько вывод основан на evidence, а насколько на prior;
- одинаковая projected probability при разной uncertainty;
- одинаковая projected probability при разном конфликте.

Пользовательский результат DSL-D должен показывать не одно число, а эпистемический профиль:

```text
Подтверждение свидетельствами
Опровержение свидетельствами
Недостаток данных
Базовая оценка
Ожидаемая подтверждённость
Конфликт источников
Покрытие формализованных утверждений
```

## 3. Неизменяемые benchmark cases

Каждый case должен содержать:

- `caseId`;
- `family`;
- `question`;
- `publicContext`;
- `goldClaims`;
- `goldQueries`;
- `minimumDslLevel`;
- `expectedFrame` для каждого применимого уровня;
- `answerRubric`;
- `requiredAbstention`;
- source и generation hashes.

Один case может иметь разные ожидаемые продукты:

- DSL-A: строгие статусы атомарных claims;
- DSL-B: те же статусы плюс proof DAG;
- DSL-C: числовые observations и comparisons;
- DSL-D: opinions и разрешённый уровень вывода.

Gold answer курса не должен переписываться при добавлении нового слоя. Новый слой только добавляет проверяемую информацию.

## 4. Экспериментальные режимы на каждом уровне

Для каждого `dslLevel` запускаются одинаковые режимы:

1. `Direct` — Codex отвечает без капсулы;
2. `FullContext` — получает релевантные данные в prompt, но без выполнения DSL;
3. `AlwaysQuery` — обязан вызвать runtime;
4. `SelfRouted` — сам решает, нужен ли запрос;
5. `Hybrid` — Codex извлекает claims и принимает управленческий trade-off, DSL проверяет атомарные premises;
6. `GoldQuery` — получает заранее правильные formal queries; измеряет чистую пользу runtime без ошибки extraction;
7. `OracleRoute` — верхняя граница выбора пути.

## 5. Разделение источников ошибки

Каждый ответ проходит через этапы:

```text
question
→ semantic interpretation
→ claim extraction
→ query construction
→ DSL runtime
→ frame interpretation
→ final answer
```

Отдельно измеряются:

- extraction error;
- predicate selection error;
- semantic-ID error;
- malformed query;
- runtime error;
- result-ignore;
- result-fabrication;
- unknown-collapse;
- conflict-collapse;
- scope-loss;
- wrong business trade-off при формально корректных premises.

Это позволяет не приписывать DSL ошибку, возникшую до его вызова.

## 6. Метрики прогрессии A→B→C→D

### Общие

- exact answer accuracy;
- atomic claim precision/recall/F1;
- rubric score;
- latency p50/p95;
- tokens;
- tool calls;
- bytes of verified frame.

### DSL-A

- strict status accuracy;
- unknown-preservation;
- conflict-preservation;
- provenance и scope accuracy.

### DSL-B

- derived-claim accuracy;
- proof completeness;
- proof faithfulness;
- cycle/unsafe-rule rejection;
- число unsupported logical leaps Codex.

### DSL-C

- unit accuracy;
- bound preservation;
- point-vs-range confusion;
- numerical policy accuracy;
- missing-measurement abstention.

### DSL-D

- корректное понимание `b,d,u,a`;
- projected-probability accuracy;
- uncertainty preservation;
- base-rate misuse;
- conflict preservation;
- overstatement относительно `allowedConclusion`;
- calibration и selective risk/coverage.

## 7. Форматы DSL-D для отдельной абляции

Одно мнение передаётся Codex четырьмя способами:

- `F0 Scalar`: только projected probability;
- `F1 Raw`: `b,d,u,a` без пояснений;
- `F2 Named`: полные названия полей;
- `F3 VerifiedFrame`: названия, projected probability, conflict, assumptions, warnings и `allowedConclusion`.

Гипотеза: `F3` будет надёжнее `F1`, потому что модель не должна самостоятельно интерпретировать и пересчитывать эпистемическую математику.

## 8. Профиль всего ответа

Нельзя усреднять opinions предложений. Нужна формальная proposition:

```text
answer_correct(answer_id)
```

Агрегатор получает:

- атомарные claims с цитатами из ответа;
- mandatory/optional;
- веса rubric;
- dependency groups;
- query hashes;
- opinions claims;
- coverage.

Наружу отдельно выдаются:

- `answerOpinion`;
- `coverage`;
- `rubricScore`;
- `decisionQuality`;
- `conflictIndex`.

Эти величины не должны сливаться в «вероятность правильности ответа».

## 9. Порядок реализации

### Milestone 1 — frozen benchmark contract

- schema case record;
- 12–20 pilot cases курса;
- gold claim decomposition;
- Direct и DSL-A baseline;
- immutable hashes.

### Milestone 2 — DSL-B

- logical-rule schema;
- deterministic reference evaluator;
- proof DAG schema;
- SWI-Prolog cross-verification;
- 10–15 derived management cases;
- A/B comparison на всех старых cases.

### Milestone 3 — DSL-C

- observation schema;
- units registry;
- point/bounded/normal kernels;
- management metrics cases;
- A/B/C comparison.

### Milestone 4 — DSL-D

- opinion schema;
- independent numerical oracle tests;
- dependency-aware fusion;
- conflict index;
- F0–F3 rendering experiment;
- answer-level profile prototype;
- A/B/C/D comparison.

## 10. Версионирование

Версии DSL и версии capsule не смешиваются:

```text
capsuleVersion: версия содержания знаний
runtimeVersion: версия исполняющего движка
dslLevel: доступный семантический слой
benchmarkVersion: замороженный набор задач
promptVersion: инструкция evaluated model
```

Пример run record:

```json
{
  "capsuleVersion": "0.1.1",
  "runtimeVersion": "0.2.0",
  "dslLevel": "DSL-B",
  "benchmarkVersion": "management-progressive-v0.1",
  "promptVersion": "hybrid-v0.1"
}
```

## 11. Критерии остановки

Слой не продвигается как научный вклад, если:

- он не улучшает ни одной заранее объявленной метрики;
- улучшение исчезает в `GoldQuery`, то есть проблема была только в extraction;
- выигрыш достигается только увеличением prompt context;
- DSL повышает точность, но ухудшает общий Pareto frontier при всех разумных cost weights;
- результат нельзя воспроизвести на другом source family;
- Codex систематически игнорирует richer frame, а verified interpretation не исправляет это.

## 12. Ближайшее действие

Активную management-капсулу не менять до прохождения экспериментального контракта DSL-B.

Сначала создать отдельный frozen management benchmark внутри `EpistemicCompilerLab/progressive-dsl/management-course`, затем реализовать DSL-B runtime и только после зелёного A/B-прогона переносить logical rules в версионированную капсулу курса.
