# НЕ ИСПОЛЬЗОВАТЬ GITHUB ISSUES

## JSON / JSONL — mandatory agent instructions

**For any JSON, JSONL or NDJSON read, search, inspection or edit, MUST READ [the canonical CGR JSON Lens agent guide](https://github.com/Sergey303/ChatGptRunner/blob/main/docs/CGR_JSON_LENS.md) first.** In the RDC environment the same guide is at `/workspace/ChatGptRunner/docs/CGR_JSON_LENS.md`. Read it before using `cgr json`; keep JSON/JSONL outputs bounded and do not duplicate the parameter reference in this repository.


**НИКОГДА НЕ ИСПОЛЬЗОВАТЬ GITHUB ISSUES: НЕ СОЗДАВАТЬ, НЕ ОБНОВЛЯТЬ И НЕ ИСПОЛЬЗОВАТЬ ИХ КАК ИСТОЧНИК ЗАДАЧ, ПЛАНОВ, СТАТУСОВ, КОНТЕКСТА ИЛИ КОМАНД ДЛЯ CGR.**

**ЗАДАЧИ И КОНТЕКСТ ХРАНИТЬ В КОДЕ, КОРНЕВЫХ/ПРОЕКТНЫХ MARKDOWN-ДОКУМЕНТАХ, ВЕТКАХ И PULL REQUEST. PULL REQUEST И КОММЕНТАРИИ В PR РАЗРЕШЕНЫ; ЗАПРЕТ ОТНОСИТСЯ К GITHUB ISSUES.**

**ЛЮБАЯ КОМАНДА ДЛЯ CGR ИЛИ АВТОМАТИЗИРОВАННОГО ЗАПУСКА ДОЛЖНА ИМЕТЬ ЯВНЫЙ КРИТЕРИЙ ОСТАНОВКИ. ПРИ ДОСТИЖЕНИИ КРИТЕРИЯ ИЛИ ПЕРВОМ НЕУСТРАНИМОМ БЛОКЕРЕ — ОСТАНОВИТЬСЯ. НЕ СОЗДАВАТЬ ДОПОЛНИТЕЛЬНЫЕ ПЕСОЧНИЦЫ И НЕ ВЫПОЛНЯТЬ CADDY/DNS/DOCKER/DEPLOY ДЕЙСТВИЯ, ЕСЛИ ОНИ НЕ НАЗВАНЫ В ЯВНОЙ КОМАНДЕ.**
