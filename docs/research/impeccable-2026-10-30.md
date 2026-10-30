# Impeccable (github.com/pbakaus/impeccable) — розбір 30.10.2026
Автор Paul Bakaus (jQuery UI, ex-Google). Apache 2.0. Виріс зі скіла Anthropic «frontend-design».
Це «дизайн-словник» для ШІ-агента: 1 скіл, 24 команди, детектор «ШІ-слопу» (62 детерміновані правила), live-режим у браузері.
- Керувати: bolder, quieter, distill, colorize, typeset, layout, **animate**, **delight**, **overdrive** (шейдери, пружинна фізика, scroll-driven анімації, View Transitions, WebGL/WebGPU).
- Перевіряти: critique (UX-оцінка), audit (доступність, швидкість, адаптивність, P0–P3).
- Доводити: polish, harden, clarify, adapt, optimize, onboard. Плюс init → PRODUCT.md, document → DESIGN.md.
- Детектор ловить: ai-color-palette, gradient-text, dark-glow, nested-cards, icon-tile-stack, kicker-above-heading, hero-eyebrow-chip, oversized-h1, overused-font, low-contrast, cramped-padding тощо.
- Принципи overdrive: спершу 2–3 напрями й вибір користувача; прогресивне покращення (без ефекту сайт усе одно гарний); 60 fps на середньому телефоні; ліниве завантаження важкого; один «вау-момент», а не десять.
- animate: рух має пояснювати стан/зв'язок; 100–150 мс відгук, 300–500 мс переходи, 500–800 мс один авторський момент; без bounce за звичкою.
Ризики встановлення: хуки, що запускаються поза підтвердженням, завантаження бінарника, телеметрія (вимикається DO_NOT_TRACK=1). Потрібна згода власника.
Для нас: бренд (#7C5CFF→#FF4F8B, #FFD60A, #4CF2FF, темний фон) лишаємо — у детекторі додати винятки (ignores) для брендових кольорів і Montserrat.
