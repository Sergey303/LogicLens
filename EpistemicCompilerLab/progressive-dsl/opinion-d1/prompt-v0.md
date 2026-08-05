# DSL-D1 exact-rational boundary experiment

Ответь на русском и верни только JSON, соответствующий output schema.

## Семантика

Биномиальное мнение задаётся как `ω=(b,d,u,a)`:

- `b` — belief: масса подтверждающего свидетельства;
- `d` — disbelief: масса опровергающего свидетельства;
- `u` — uncertainty: нераспределённая масса из-за недостатка свидетельств;
- `a` — base rate: априорная доля, используемая только для проекции неопределённости.

Инварианты:

- `b+d+u=1` проверяется в точной арифметике;
- `p=b+a*u`;
- `a` не является новым evidence;
- `u` не является вероятностью ошибки;
- conflict index хранится отдельно от `u`;
- fusion источников запрещено без явной policy.

## D1 policy

Применяй правила строго по порядку к тому представлению, которое доступно в текущем условии:

1. `conflictIndex >= 1/2` → `report_conflict`, action `report_conflict`, `withholdsAssertiveDecision=true`;
2. `u >= 1/2` → `abstain_high_uncertainty`, action `abstain`, `withholdsAssertiveDecision=true`;
3. `p >= 3/4`, `b >= 1/2`, `u <= 1/4` → `assert_with_evidence`, action `answer_with_epistemic_profile`, `withholdsAssertiveDecision=false`;
4. `p <= 1/4`, `d >= 1/2`, `u <= 1/4` → `qualified_refutation`, action `explain_refutation_with_profile`, `withholdsAssertiveDecision=false`;
5. `p >= 13/20`, `b < 1/2`, `u < 1/2` → `qualify_prior_sensitive`, action `answer_with_prior_warning`, `withholdsAssertiveDecision=false`;
6. иначе → `qualified_uncertain`, action `answer_with_uncertainty`, `withholdsAssertiveDecision=true`.

## Условия

- `scalar`: доступна только округлённая projected probability. Не восстанавливай остальные числа. Верни `scalar_insufficient`, action `abstain_on_scalar`.
- `rounded`: доступны только десятичные `b,d,u,a,conflict` при объявленной precision. Считай эти десятичные числа точными для данного условия, вычисли p и примени policy.
- `exact`: доступны точные дроби numerator/denominator без готового вывода. Выполни точную рациональную арифметику. Если точные дроби отсутствуют, верни `request_exact_opinion`, action `abstain_and_request_exact_opinion`.
- `verified`: verified frame авторитетен. Перенеси точные и десятичные значения, exact conclusion/action и boundary metadata без усиления.

## Поля ответа

- decimal fields (`belief` ... `conflictIndex`) заполняй доступными десятичными значениями; недоступные — пустая строка;
- exact fields (`exactBelief` ... `exactConflictIndex`) записывай канонически как `numerator/denominator`; недоступные — пустая строка;
- `roundedInvariantPreserved` показывает, равна ли сумма доступных rounded `b+d+u` точно 1;
- `exactInvariantPreserved` показывает, равна ли сумма доступных exact дробей точно 1; если exact недоступен — false;
- `recognizedRoundingCollision=true`, только если ввод явно сообщает, что rounded и exact policy outcomes различаются, либо ты сам это установил при наличии обеих форм;
- `withholdsAssertiveDecision` означает, что ответ не утверждает и не опровергает proposition; conflict report считается withholding, хотя сообщение пользователю всё равно формируется;
- `answerLevelProfile=true` только для формализованной proposition уровня всего ответа;
- не выполняй скрытое fusion.

Экспериментальный ввод находится ниже.
