"""Пульт ШІкарно ↔ Telegram-бот. python3 inbox.py  — забрати нові особисті повідомлення боту.
Повідомлення з груп/каналу пропускаються. Власник: owner.json {chat_id}; перший /start ще ПІДТВЕРДЖУЄТЬСЯ
власником на пульті (не довіряти автоматично). Нові повідомлення → inbox.json (append) і друк."""
import sys,json,os;sys.path.insert(0,'/home/claude/tg');import tg
D='/home/claude/tg'; OFF=D+'/offset.txt'; INB=D+'/inbox.json'; OWN=D+'/owner.json'
def load(p,d):
    try: return json.load(open(p))
    except Exception: return d
def updates():
    """Оновлення бота. З 27.10 бот на вебхуку пульта (pult/worker.js): забираємо чергу звідти; без вебхука — getUpdates."""
    if tg.call('getWebhookInfo')['result'].get('url'):
        sys.path.insert(0,'/home/claude/pult'); import pultlib
        r=pultlib.send('/api/tg/pull',{})['updates']
        if r:
            raw=load(D+'/updates.json',[]); raw=(raw+r)[-500:]; json.dump(raw,open(D+'/updates.json','w'),ensure_ascii=False)  # усе, включно з групою — для модерації
        return r,None
    off=int(open(OFF).read()) if os.path.exists(OFF) else 0
    return tg.call('getUpdates',offset=off,limit=100,timeout=0)['result'],off
def fetch():
    r,off=updates(); new=[]
    for u in r:
        if off is not None: off=u['update_id']+1
        m=u.get('message') or u.get('edited_message')
        if m and m['chat']['type']=='private':
            new.append(dict(update_id=u['update_id'],chat_id=m['chat']['id'],user=m['from'].get('username'),name=m['from'].get('first_name'),date=m['date'],text=(m.get('text') or m.get('caption') or '')+(' [фото]' if m.get('photo') else '')+(' [файл]' if m.get('document') or m.get('video') else '')))
    if off is not None: open(OFF,'w').write(str(off))
    inbox=load(INB,[]); inbox+=new; json.dump(inbox,open(INB,'w'),ensure_ascii=False,indent=1)
    return new
def ask(text):
    o=load(OWN,{})
    if not o.get('chat_id') or not o.get('confirmed'): return None
    return tg.call('sendMessage',chat_id=o['chat_id'],text=text,parse_mode='HTML')
if __name__=='__main__':
    for m in fetch(): print(json.dumps(m,ensure_ascii=False))
    print('owner:',load(OWN,{}))
