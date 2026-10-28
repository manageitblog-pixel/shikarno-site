"""Вартовий бота: опитує чергу вебхука (pult /api/tg/pull через inbox.fetch) кожні 10 с.
Щойно приходить особисте повідомлення від власника — друкує його і виходить: завершення фонового процесу будить сесію Claude.
Запуск (у фоні, перезапускати наприкінці кожного ходу): python3 /home/claude/tg/watch.py
Максимум ~110 хв роботи (ліміт фонової команди 2 год) → вихід з TIMEOUT, сесія прокидається і перезапускає вартового."""
import sys, time, json
sys.path.insert(0, '/home/claude/tg'); import inbox
OWNER = inbox.load(inbox.OWN, {}).get('chat_id')
end = time.time() + 110 * 60
while time.time() < end:
    try:
        new = inbox.fetch()
    except Exception as e:
        new = []; print('err', e, file=sys.stderr)
    mine = [m for m in new if m.get('chat_id') == OWNER]
    if mine:
        for m in mine: print(json.dumps(m, ensure_ascii=False))
        print('OWNER_MESSAGE'); sys.exit(0)
    time.sleep(10)
print('TIMEOUT')
