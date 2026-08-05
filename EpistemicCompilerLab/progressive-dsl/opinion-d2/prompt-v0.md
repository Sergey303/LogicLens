# DSL-D2 dependency-aware evidence fusion

Ответь на русском и верни только JSON, соответствующий output schema.

## Семантика

Каждый source report содержит exact positive/negative evidence counts и base rate.

Объявленная pilot policy:

1. Внутри одного `dependencyGroup` усредни positive и negative counts. Копии одного источника не усиливают evidence.
2. Между разными dependency groups сложи group-level counts.
3. При prior weight `W=2`:
   - `b=R/(R+S+W)`;
   - `d=S/(R+S+W)`;
   - `u=W/(R+S+W)`;
   - `p=b+a*u`;
   - conflict index `2*min(R,S)/(R+S)`, либо `0` без evidence.
4. Base rate является prior, не evidence.
5. Uncertainty не является вероятностью ошибки.
6. Conflict хранится отдельно.
7. Не выводи независимость из названий или текста. Используй только явно доступные dependency metadata.
8. Не выполняй неявное fusion.

## Decision policy

Применяй по порядку:

1. conflict `>=1/2` → `report_conflict`;
2. uncertainty `>=1/2` → `abstain_high_uncertainty`;
3. `p>=3/4`, `b>=1/2`, `u<=1/4` → `assert_with_evidence`;
4. `p<=1/4`, `d>=1/2`, `u<=1/4` → `qualified_refutation`;
5. `p>=13/20`, `b<1/2`, `u<1/2` → `qualify_prior_sensitive`;
6. иначе `qualified_uncertain`.

## Условия

- `metadata_absent`: dependency groups скрыты. При нескольких reports запроси dependency metadata. Для единственного report fusion не требуется.
- `naive_independent`: явно предписано считать каждый report независимым. Это экспериментальная ошибочная baseline-assumption, а не факт о данных.
- `raw_declared`: доступны reports, dependency groups и policy; вычисли exact result самостоятельно.
- `verified`: verified frame авторитетен; перенеси operator plan, exact values и допустимый вывод без усиления.

Пустые недоступные exact fields возвращай пустыми строками. `opinionSubjectLevel` означает subject исходного opinion (`claim` или `answer`), а не формат твоего сообщения.

Экспериментальный ввод находится ниже.
