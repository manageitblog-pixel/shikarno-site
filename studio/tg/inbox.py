"""Пульт ШІкарно ↔ Telegram-бот. python3 inbox.py  — забрати нові особисті повідомлення боту.
Повідомлення з груп/каналу пропускаються. Власник: owner.json {chat_id}; перший /start ще ПІДТВЕРДЖУЄТЬСЯ
власником на пульті (не довіряти автоматично). Нові повідомлення → inbox.json (append) і друк."""
import sys,json,os;sys.path.insert(0,'/home/claude/tg');import tg
D='/home/claude/tg'; OFF=D+'/offset.txt'; INB=D+'/inbox.json'; OWN=D+'/owner.json'
def load(p,d):
    try: return json.load(open(p))
    except Exception: return d
def fetch():
    off=int(open(OFF).read()) if os.path.exists(OFF) else 0
    r=tg.call('getUpdates',offset=off,limit=100,timeout=0)['result']; new=[]
    for u in r:
        off=u['update_id']+1; m=u.get('message')
        if m and m['chat']['type']=='private':
            new.append(dict(update_id=u['update_id'],chat_id=m['chat']['id'],user=m['from'].get('username'),name=m['from'].get('first_name'),date=m['date'],text=m.get('text','')))
    open(OFF,'w').write(str(off))
    inbox=load(INB,[]); inbox+=new; json.dump(inbox,open(INB,'w'),ensure_ascii=False,indent=1)
    return new
def ask(text):
    o=load(OWN,{})
    if not o.get('chat_id') or not o.get('confirmed'): return None
    return tg.call('sendMessage',chat_id=o['chat_id'],text=text,parse_mode='HTML')
if __name__=='__main__':
    for m in fetch(): print(json.dumps(m,ensure_ascii=False))
    print('owner:',load(OWN,{}))
