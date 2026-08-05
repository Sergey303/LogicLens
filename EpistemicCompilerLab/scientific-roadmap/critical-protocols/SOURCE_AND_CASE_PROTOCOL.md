# Source and Case Protocol
Статус: **MUST complete before split creation**
## 1. Source registration
Для каждого source family создать запись:
```text
source_family_id
domain_id
publisher
title
version
retrieved_at
license
content_hash
local_path
allowed_publication_form
replication_only
```
Порядок:
1. Зафиксировать источник до создания cases.
2. Вычислить SHA-256 исходного файла.
3. Записать лицензионное решение.
4. Назначить `source_family_id`.
5. Индексировать evidence до страницы/секции/span.
STOP, если источник нельзя независимо проверить или легально использовать.
## 2. Base scenario
Один `base_scenario_id` описывает одну логическую ситуацию. Парафразы не считаются независимыми scenarios.
Каждый case MUST содержать:
```text
case_id
base_scenario_id
domain_id
source_family_id
entity_family_id
rule_template_id
paraphrase_family_id
difficulty_strata
question
gold_interpretation
gold_query
gold_frame
acceptable_alternatives
source_refs
split
```
## 3. Gold construction
MUST:
1. Сначала создать source-bound assertions.
2. Затем независимо записать interpretation.
3. Затем query.
4. Затем gold frame.
5. Затем acceptable alternatives.
6. Только после этого создавать natural-language paraphrases.
Запрещено:
- создавать gold frame production compiler;
- выводить gold из model output;
- менять gold после просмотра model answer;
- копировать expected fields в student-visible record;
- использовать одинаковый template с переименованными сущностями как независимую семью.
## 4. Required case coverage
Для каждого domain и confirmatory split обеспечить:
```text
supported   >= 15%
refuted     >= 15%
unknown     >= 15%
conflicting >= 15%
```
MUST включить:
- missing obligatory field;
- version/scope ambiguity;
- one-hop и multi-hop rules;
- irrelevant distractors;
- explicit source conflict;
- malformed-but-rejectable query;
- open-world unknown;
- explicit negative evidence.
STOP, если primary status отсутствует в HOLDOUT или REPLICATION.
## 5. Annotation
Для real-source cases:
1. Annotator A создаёт interpretation/query/frame.
2. Annotator B проверяет независимо, не видя A.
3. Disagreement фиксируется до обсуждения.
4. Adjudicator выбирает решение или несколько допустимых.
5. Спорный case без доказанного gold исключается по заранее заданному правилу.
Report MUST contain:
```text
agreement before adjudication
disagreement count
multi-valid count
excluded ambiguity count
```
## 6. Source extraction separation
Formal correctness не доказывает source extraction correctness.
MUST хранить отдельно:
```text
raw source
source span
candidate assertion
accepted assertion
validation result
human audit result
```
Любой assertion без addressable provenance запрещён в confirmatory benchmark.
## 7. Case acceptance gate
Case принимается, только если:
- schema valid;
- source refs resolve;
- gold independently reviewed;
- status/rule/scope labels assigned;
- no expected field leaks to visible input;
- acceptable alternatives explicit;
- licensing disposition recorded.
Изменение accepted gold создаёт новую case version и требует повторной проверки leakage.
