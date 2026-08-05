# Критические протоколы флагманской статьи
Статус: **обязательные нормативные инструкции**  
Целевая статья: **Compile, Don’t Teach: Verified Epistemic Interfaces for Fixed-Weight Small Language Models**
## 1. Приоритет документов
При конфликте использовать порядок:
1. `../TARGET_PAPER_COMPILE_DONT_TEACH.md` — допустимый научный тезис;
2. `../TARGET_PAPER_FULL_EXECUTION_PATH_AND_STRICT_AUDIT.md` — полный критический путь;
3. этот каталог — однозначные инструкции исполнения;
4. task/issue/commit messages — только реализация, не изменение протокола.
Исполнитель не вправе ослаблять MUST/STOP-условия локальным решением.
## 2. Обязательные протоколы
- [`SOURCE_AND_CASE_PROTOCOL.md`](SOURCE_AND_CASE_PROTOCOL.md) — источники, cases и разметка;
- [`SPLIT_LEAKAGE_AND_FREEZE_PROTOCOL.md`](SPLIT_LEAKAGE_AND_FREEZE_PROTOCOL.md) — splits, leakage и freeze;
- [`ORACLE_AND_SCORER_PROTOCOL.md`](ORACLE_AND_SCORER_PROTOCOL.md) — независимый oracle и scorer;
- [`STATISTICS_AND_ANALYSIS_PROTOCOL.md`](STATISTICS_AND_ANALYSIS_PROTOCOL.md) — power, primary analysis и интерпретация;
- [`MODEL_AND_RUN_PROTOCOL.md`](MODEL_AND_RUN_PROTOCOL.md) — модели, modes и запуск;
- [`TEACHER_PROTOCOL.md`](TEACHER_PROTOCOL.md) — Codex/teacher-loop;
- [`SUBMISSION_AND_REVIEW_PROTOCOL.md`](SUBMISSION_AND_REVIEW_PROTOCOL.md) — HOLDOUT, replication, artifact и review.
## 3. Универсальная форма любого этапа
Каждый этап обязан иметь:
```text
INPUTS
ACTION
MACHINE-CHECKABLE OUTPUTS
FORBIDDEN ACTIONS
PASS GATE
STOP/PIVOT RULE
```
Этап без одного из этих блоков считается неописанным и не запускается.
## 4. Универсальные запреты
- Не смотреть HOLDOUT или REPLICATION до разрешённой фазы.
- Не исправлять model output до scoring.
- Не удалять failures, timeouts, malformed JSON или rejected candidates.
- Не менять одновременно два causal factors вне declared combined ablation.
- Не использовать результаты pilot 18/18 и 24/24 как независимый confirmatory evidence.
- Не утверждать privacy, learning или formal correctness шире измеренного контракта.
- Не использовать closed teacher как единственную опору central claim.
- Не подавать статью при незакрытом Blocker.
## 5. Definition of protocol compliance
Работа compliant, только если:
- каждый run имеет immutable manifest;
- каждый artifact имеет hash;
- каждый exclusion соответствует preregistered rule;
- primary endpoint вычисляется одним frozen scorer;
- causal contrast имеет matched control;
- oracle независим от production implementation;
- abstract claims связаны с конкретными таблицами;
- отрицательные результаты сохранены;
- clean-room reproduction завершена до submission.
Нарушение benchmark isolation аннулирует затронутый confirmatory run.
