# Policy shadow: звіт №1 (22.11.2026, ~14:50Z)

План: `docs/org/autonomy-plan-2026-11-22.md`, §11 крок 3. Режим `policy.json.mode = "shadow"`. Policy ще ніхто не викликає: вбудовування в `yt.py`/`tg.py` буде кроком 4, після 25.11 ~18:00Z.
Прогін був лише на читання: `python3 studio/policy.py check <ep> --action youtube_upload` (без `--record`). Нічого не опубліковано, у `ops.sqlite` нічого не записано, зовнішніх API не викликали.

## Що сказав би enforce

| Епізод | Вихід | Вердикт enforce | Чому (rules_triggered) |
|---|---|---|---|
| ep78_signal_shi_agent | 25.11 17Z (уже заплановано) | **BLOCK** | `duplicate.publication_exists` + `duplicate.slug_uploaded`: відео вже залито (Rlm1u-I6x00), тож повторний upload був би дублем. `quality.short_above_target` DEGRADE: 48,7 с > 35 с, тому без TikTok до canary. Факт-файл PASS. |
| ep81_tier_kids | 23.11 17Z (уже заплановано) | **BLOCK** | Дубль, як у ep78 (xaYHobFNYHo). `high_risk.requirements` BLOCK: тема «діти», а частка tier-1 джерел 0,83 < 1,0 (dou.ua — tier-2). |
| ep82_tier_kitchen | 24.11 17Z | **BLOCK** | `quality.no_render`: немає `final.mp4`. `fact.stale` DEGRADE: `ep82.py` змінено о 13:23Z, а фактчек зроблено о 12:47Z. `high_risk.topic` DEGRADE: калорії, дисклеймер є. `publication.no_idea_link` DEGRADE. Fact: ALLOW (останній рядок «Вердикт: PASS», 2 × «не заявлено»). |
| ep83_moonlock_chesno | 26.11 17Z | **BLOCK** | `fact.unverified_claimed` = 1: «у «Небажані»» в описі має статус UNVERIFIED (дрібне), і в META.description його досі не виправлено. Плюс `quality.no_render`. |
| ep84_prof_logoped | 27.11 17Z | **BLOCK** | Лише `quality.no_render`. `high_risk.topic` (діти) DEGRADE: tier-1 100 %, UNVERIFIED «не заявлено». Fact: ALLOW. |
| guide1 | 25.11 17Z | **BLOCK** | `fact.no_verdict`: останній рядок не «Вердикт:», а «## Вердикт: FAIL → … → PASS» усередині файлу. `fact.fail_rows` = 2 (сегменти 14 і 34), повторної перевірки немає. `fact.unverified_claimed` = 1 (сегм. 41). `quality.no_render`. `high_risk.requirements`. `schedule_conflict.slot_taken` RETRY_LATER: 25.11 17Z уже зайнято ep78, наступний вільний слот за `publications` — 26.11 17Z (але там ep83, який ще не залито, тож policy його поки не бачить → реально 28.11 або інший день). |
| guide3 | 9.12 17Z | **BLOCK** | Лише `quality.no_render`. Fact: ALLOW: 3 FAIL першого раунду закрито таблицею повторної перевірки, останній рядок «Вердикт: PASS». `high_risk.topic` DEGRADE, `publication.no_idea_link` DEGRADE. |

**Підсумок:** 7 BLOCK. Справжніх блокерів контенту три:
- guide1: формат факт-файлу, 2 FAIL без повторної перевірки, 1 UNVERIFIED і конфлікт слоту з ep78.
  - **виправлено 22.11:** файл отримав раунди 2–3 і `Вердикт: PASS`; парсер більше не рахує UNVERIFIED/FAIL, закриті PASS у пізнішому раунді (сегмент/формулювання) → `fact` ALLOW. Лишаються `quality.no_render`, `high_risk.requirements`, `schedule_conflict.slot_taken`, `publication.no_idea_link`. Тести policy — на фікстурах studio/tests/fixtures/.
- ep83: UNVERIFIED в описі.
- ep82: застарілий фактчек (DEGRADE).

ep82, ep83, ep84, guide1 і guide3 блокує ще й відсутній рендер. Це очікувано, бо їх ще не зібрали; після `build.sh` і `audit_vo.py --json` перевірку треба повторити. ep78 і ep81 вже залиті, тож для них BLOCK на `youtube_upload` правильний: повторна заливка була б дублем.

## Що зробити до 25.11, щоб enforce не заблокував
1. **guide1.** Попросити незалежного фактчекера повторно перевірити сегменти 14, 34 і 41 і дописати в кінець файлу таблицю повторної перевірки та останній рядок `Вердикт: PASS`. Розвести слот з ep78 (25.11 17Z).
2. **ep83.** В описі (`ep83.py` META) замінити «у «Небажані»» на «у папку Junk («Небажані»)», як рекомендував фактчекер, і після правки перезапустити фактчек.
3. **ep82.** Повторно перевірити зміни в `ep82.py` після 12:47Z, бо файл змінили вже після фактчеку.
4. Перед заливкою кожного нового епізоду запускати `audit_vo.py <ep> --json`. Без `audit_vo.json` у теці епізоду quality дає BLOCK `asr_missing`; legacy-епізодів це не стосується.

## Калібрування (зміни порогів відносно плану; детальніше в `_why` у policy.json)
- `long_min_s` = 240 с замість 360. Дайджест триває 4–6 хв (RUNBOOK), і поріг 360 с його заблокував би.
- `max_unverified_not_claimed` = 5. Рішення власника №3 дозволяє UNVERIFIED з позначкою «не заявлено»; межа 5 лишилась як запобіжник. Позначку «не заявлено» шукаємо в колонці статусу і в примітці (ep84).
- Для high-risk допускаємо ≤2 «не заявлено» замість 0. Тест §12 п.1 вимагає, щоб ep82 мав DEGRADE, а не BLOCK.
- З high-risk прибрали загальні «здоров'я» і «суд». У гайдах це застереження, а не тема.
- Фактчек ділиться на раунди за рядками `Вердикт:`. FAIL рахуємо лише в останньому раунді, тобто після повторної перевірки, а UNVERIFIED — у всіх раундах.
- Відсутній `IDEA_ID` / «ідея #N» дає DEGRADE, а не BLOCK, доки ідеї не перенесено в нову схему.

## Як відтворити
```bash
python3 studio/policy.py check ep82 --action youtube_upload [--json]   # лише читання
python3 studio/policy.py check ep82 --action youtube_upload --record   # gate(): рядок в ops.sqlite, shadow → proceed
python3 studio/policy.py replay <decision_id>                          # детермінований повтор з input_snapshot
python3 studio/policy.py explain [fact|quality|...]                    # пороги + джерело кожного
```
Наступний звіт shadow: після кроку 4 (gate у `yt.py`/`tg.py` після 25.11 18Z), за 3–5 днів, порівняння «що сказав policy» з тим, що сталося насправді.
