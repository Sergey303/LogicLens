# Split, Leakage and Freeze Protocol
Статус: **MUST complete before teacher optimization**
## 1. Grouped split
Split выполнять по группам, а не по вопросам:
```text
source_family_id
entity_family_id
rule_template_id
document_version
paraphrase_family_id
```
Порядок:
1. Зафиксировать grouping keys.
2. Зафиксировать split seed.
3. Создать TRAIN/DEV/HOLDOUT.
4. Назначить REPLICATION из независимой source family.
5. Проверить balance.
6. Записать manifest и hashes.
7. Переместить sealed splits в недоступное tooling-хранилище.
Нельзя перебалансировать split после просмотра model performance.
## 2. Visibility contract
```text
TRAIN: labeled content may be teacher-visible
DEV: content hidden; aggregate metrics only
HOLDOUT: sealed
REPLICATION: separately sealed
```
Teacher tooling MUST физически запрещать чтение sealed paths.
Developer RAG, repository search и indexing MUST исключать sealed content.
## 3. Leakage audit
До freeze выполнить:
- exact duplicate search;
- normalized duplicate search;
- semantic near-duplicate search;
- shared source span detection;
- shared rule graph detection;
- shared generated seed detection;
- prompt/log scan for case IDs and expected fields;
- RAG/index exclusion verification;
- teacher-tool permission test.
Каждое совпадение получает disposition:
```text
safe
move_group
remove_case
block_freeze
```
Необъяснённое совпадение между TRAIN/DEV и HOLDOUT/REPLICATION блокирует freeze.
## 4. Canary test
В sealed data добавить non-semantic canary markers.
MUST:
1. хранить canary registry отдельно;
2. сканировать все teacher-visible prompts/logs/artifacts;
3. останавливать run при совпадении;
4. считать затронутый confirmatory batch недействительным;
5. расследовать путь утечки до нового freeze.
## 5. Power-based size
Число scenarios определяется simulation, не желаемым круглым числом.
Порядок:
1. Получить DEV-only variance estimate.
2. Задать smallest effect of interest.
3. Моделировать paired discordance и scenario clustering.
4. Требовать target power `>= 0.90`.
5. Добавить reserve cases до freeze.
6. Зафиксировать итоговый размер.
Запрещено увеличивать dataset после HOLDOUT ради significance.
## 6. Freeze manifest
Manifest MUST contain hashes for:
```text
sources
cases
split assignment
schemas
parser
prompts
knowledge
policies
oracle
scorer
analysis scripts
model profiles
```
HOLDOUT freeze разрешён, только если:
- licenses reviewed;
- case audit passed;
- balance passed;
- leakage report has zero Blockers;
- power target passed;
- sealed paths inaccessible;
- manifests reproducibly validate.
## 7. Change policy
После freeze:
- scientific-choice changes запрещены;
- bug fix записывается отдельным audit record;
- affected modes rerun symmetrically;
- changed sealed case creates new benchmark version;
- previous result loses confirmatory status.
## 8. STOP rules
STOP and invalidate affected batch when:
- sealed hash changed;
- canary appeared outside sealed storage;
- expected field reached student/teacher;
- split groups overlap;
- HOLDOUT was viewed before authorized phase;
- exclusion rule was invented after seeing result.
