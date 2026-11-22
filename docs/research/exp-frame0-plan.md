# Експеримент exp-2026-11-22-frame0: план старту

Підготував Data Engineer 22.11.2026 (21:05 Київ). Статус у `ops.sqlite` поки `designed`, тож **не стартовано**.
Старт робить продакшн 24.11, одразу після заливки ep82 (прем'єра 24.11 17:00Z).

## Дизайн (вичитано в БД до старту)

Після `exp start` тригер `exp_frozen` блокує зміни hypothesis, variant, control, threshold і success_metric.
Зміни нижче внесено, поки статус `designed`. Кожна записана в `agent_decisions` (`decision_type='experiment'`, `action=redesign`, з before/after і причиною).

| поле | було | стало |
|---|---|---|
| success_metric | `viewed_vs_swiped (Studio) / частка SHORTS-трафіку` | `частка SHORTS-трафіку і перегляди 48 год vs медіана контролю` |
| threshold | `+5 п.п. до медіани контролю` | `+20% до медіани переглядів 48 год контролю і частка SHORTS ≥ контролю` |
| hypothesis | «…дає більше «переглянули/гортали»…» | те саме + «вимірюємо проксі з API: перегляди за 48 год і частка SHORTS-трафіку» |

Чому так. `viewed_vs_swiped` є лише в YouTube Studio. YouTube Analytics API його не віддає, і в лейку цієї метрики немає, тому детерміновано її не порахувати. Поріг «+5 п.п.» стосувався саме цієї метрики. Гіпотезу Дизайнера по суті не змінено, лише названо проксі.
Guardrail залишився тим самим: `avg_pct не нижче контролю −5 п.п.` Він коректний після виправлення `daily.avg_pct=0 → NULL` (245 рядків, 22.11).

Як рахувати (детерміновано, з `studio/data/analytics.sqlite`):
- **перегляди 48 год** = `sum(daily.views)` за дату публікації (UTC) і наступний день;
- **частка SHORTS** = `traffic_daily` source='SHORTS' / усі джерела за ті самі 2 дні;
- **avg_pct** = `sum(views*avg_pct)/sum(views where avg_pct is not null)` за 7 днів (NULL = API не дав утримання);
- рішення приймається не раніше ніж `end_date + 3 дні` (тобто 02.12), бо дані API запізнюються на 2–3 дні.

## Variant (5 = sample_size)

ep82_tier_kitchen (24.11), далі ep83, ep84, ep85, ep86. У всіх `FRAME0=True` (ep82: тір-лист, frame0 за замовчуванням у `Generic.tsx`).
На старті у variant лише ep82. Решту додавати командою `exp add` після кожної заливки.

## Control: 10 останніх опублікованих Shorts зі старим кадром 0

Новий кадр 0 з'явився в коміті `2f94528` (22.11 13:36Z). У попередньому коміті `550b191` (13:25Z) `frame0` у `Generic.tsx` ще немає.
Дати рендеру: `ep80_prof_olx/final.mp4` 22.11 06:55Z, `ep81_tier_kids/final.mp4` 22.11 12:32Z, обидва **до** коміту.
`props.json` ep81 не містить `frame0`. Кадр 0 (t=0.2 с) ep79, ep80 і ep81 я перевірив візуально: це старий кадр (заголовок + таблиця, без великого Байта).
Отже, ep80 і ep81 беремо в контроль. До 24.11 обидва вже вийдуть: ep80 22.11 17Z, ep81 23.11 17Z.

| # | content_id | YouTube | вихід (UTC) | формат |
|---|---|---|---|---|
| 1 | ep81_tier_kids | xaYHobFNYHo | 23.11 17:00 | tier |
| 2 | ep80_prof_olx | LtNuOtQe0pc | 22.11 17:00 | prof |
| 3 | ep79_tier_money | gljrHADi4aU | 21.11 17:00 | sec/tier |
| 4 | ep77_sms_shakhrai | CfHTFrYH_z4 | 20.11 17:00 | sec |
| 5 | ep76_inkognito_shi | 0Kb6AamTRQo | 19.11 17:00 | sec |
| 6 | ep75_lovable_vytik | Bh-YF2BbuiQ | 15.11 17:00 | sec |
| 7 | ep74_chatgpt_wallet | ZSOH2sXLI_Y | 14.11 12:00 | sec |
| 8 | ep73_syayvo_kyivstar | Vv5pl-AFtgA | 14.11 08:00 | news |
| 9 | ep72_claude_meetings | trlZL_IoPkE | 13.11 17:00 | news |
| 10 | ep71_gemini_hydrogen | KRm46ScK2Bc | 13.11 12:00 | free |

Не взято:
- **cut6_c1/c2/c3** (16–18.11). Це нарізки з довгого `pryvatnist1` з оверлеєм, а не шаблон `Generic.tsx`, тому «старого кадру 0» у них немає, і порівняння було б некоректним.
- **ep78_signal_shi_agent**. Рендер старий (21.11), але прем'єра 25.11, тобто всередині вікна експерименту, а контроль у дизайні означає «попередні».
  Його можна додати пізніше як паралельний контроль (`exp add … ep78_signal_shi_agent --arm control`), якщо Дизайнер/DA погодять.
- Довгі (weekly2, pryvatnist1, konektory1, scion1), бо це не Shorts.

Попередній зріз контролю станом на 22.11 (лейк відстає на 3 дні, ep77–ep81 ще без повних даних): медіана переглядів 48 год = 22 (n=5), медіана частки SHORTS за весь час = 46% (n=6).
Під час рішення медіану треба **перерахувати** на всіх 10.

## Команда старту (виконує продакшн 24.11 після заливки ep82)

```bash
python3 studio/ops.py exp start exp-2026-11-22-frame0 --date 2026-11-24 --agent production \
  --control ep81_tier_kids,ep80_prof_olx,ep79_tier_money,ep77_sms_shakhrai,ep76_inkognito_shi,ep75_lovable_vytik,ep74_chatgpt_wallet,ep73_syayvo_kyivstar,ep72_claude_meetings,ep71_gemini_hydrogen \
  --variant ep82_tier_kitchen
python3 studio/ops.py exp status exp-2026-11-22-frame0
```

Після заливки кожного з ep83–ep86 (content_id = slug теки в `/home/claude/eps`):

```bash
python3 studio/ops.py exp add exp-2026-11-22-frame0 <ep83_slug> --agent production
```

`exp start` повторно не спрацює (ValueError). Variant понад `sample_size=5` теж буде відхилено.
Для варіанта проставляється `publications.experiment_id`, якщо картка вже є в `publications`.
