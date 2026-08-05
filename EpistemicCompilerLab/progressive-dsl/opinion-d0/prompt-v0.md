# DSL-D0 opinion-frame experiment

Ответь на русском и верни только JSON, соответствующий output schema.

## Семантика

Биномиальное мнение задаётся как `ω=(b,d,u,a)`:

- `b` — belief: масса подтверждающего свидетельства;
- `d` — disbelief: масса опровергающего свидетельства;
- `u` — uncertainty: нераспределённая масса из-за недостатка свидетельств;
- `a` — base rate: априорная доля, используемая только для проекции неопределённости.

Обязательные инварианты:

- `b+d+u=1`;
- `a` не входит в эту сумму и не является новым evidence;
- projected probability `p=b+a*u`;
- `u` не является вероятностью ошибки;
- conflict index хранится отдельно от `u`;
- одинаковая `p` не означает одинаковую уверенность или одинаковый допустимый вывод;
- не выполняй fusion источников без явно разрешённой fusion policy.

## D0 decision policy

Применяй правила в указанном порядке:

1. `conflictIndex >= 0.5` → `report_conflict`, action `report_conflict`;
2. `u >= 0.5` → `abstain_high_uncertainty`, action `abstain`;
3. `p >= 0.75`, `b >= 0.5`, `u <= 0.25` → `assert_with_evidence`, action `answer_with_epistemic_profile`;
4. `p <= 0.25`, `d >= 0.5`, `u <= 0.25` → `qualified_refutation`, action `explain_refutation_with_profile`;
5. `p >= 0.65`, `b < 0.5`, `u < 0.5` → `qualify_prior_sensitive`, action `answer_with_prior_warning`;
6. иначе → `qualified_uncertain`, action `answer_with_uncertainty`.

## Условия эксперимента

- `direct`: opinion недоступно. Не угадывай числа; conclusion `request_opinion`, action `abstain_and_request_opinion`.
- `scalar`: доступна только projected probability. Не восстанавливай `b,d,u,a` или conflict; conclusion `scalar_insufficient`, action `abstain_on_scalar`.
- `raw`: доступны `b,d,u,a`, conflict и scope, но нет готового вывода. Вычисли `p` и примени D0 policy.
- `verified`: verified frame авторитетен. Перенеси числа и допустимый вывод без усиления.

Пустые недоступные числовые поля возвращай как пустую строку.

`sameProjectionCanDiffer` должен быть true, когда тебе доступна семантика полного opinion; один scalar не позволяет доказать различие конкретного случая.

Для answer-level opinion явно скажи, что профиль относится к формализованной proposition `answer_correct`, а не доказывает истинность каждого предложения текста.

Экспериментальный ввод находится ниже.
