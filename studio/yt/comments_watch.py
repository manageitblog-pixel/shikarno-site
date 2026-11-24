"""Моніторинг коментарів YouTube без нашої відповіді (власник 24.11: «Став задачу на постійний моніторинг»).
Читає останні треди каналу (commentThreads, 1 од. квоти на сторінку) і друкує ті, де автор — не ми і нашої відповіді немає.
Вихід: рядки «UNANSWERED <published> <videoId> <threadId> | <автор> | <текст>»; код 1, якщо є такі.
Відповідь — через studio/yt/comments_watch.py reply <threadId> "<текст>" (за правилом RUNBOOK «ВІДПОВІДІ НА КОМЕНТАРІ»)."""
import sys, json, os
SKIP = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'comments_skip.json')
sys.path.insert(0, '/home/claude/yt'); import yt


def me():
    return yt.api('channels', part='id', mine='true')['items'][0]['id']


def unanswered(pages=2):
    ch = me(); out = []; tok = None
    skip = json.load(open(SKIP)) if os.path.exists(SKIP) else {}
    for _ in range(pages):
        q = dict(part='snippet,replies', allThreadsRelatedToChannelId=ch, maxResults=100, order='time')
        if tok: q['pageToken'] = tok
        r = yt.api('commentThreads', **q)
        for t in r.get('items', []):
            s = t['snippet']; c = s['topLevelComment']['snippet']
            if c.get('authorChannelId', {}).get('value') == ch or t['id'] in skip: continue
            reps = t.get('replies', {}).get('comments', [])
            if any(x['snippet'].get('authorChannelId', {}).get('value') == ch for x in reps): continue
            if s['totalReplyCount'] > len(reps): continue  # не всі відповіді в відповіді API — пропускаємо, щоб не дублювати
            out.append((c['publishedAt'][:16], s['videoId'], t['id'], c['authorDisplayName'], c['textOriginal'].replace('\n', ' ')[:300]))
        tok = r.get('nextPageToken')
        if not tok: break
    return out


def reply(thread_id, text):
    body = {'snippet': {'parentId': thread_id, 'textOriginal': text}}
    r = yt._req('https://www.googleapis.com/youtube/v3/comments?part=snippet', data=json.dumps(body).encode(),
                headers={'Authorization': 'Bearer ' + yt.token(), 'Content-Type': 'application/json'})
    return json.load(r)


if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[1] == 'reply':
        print('replied', reply(sys.argv[2], sys.argv[3]).get('id')); sys.exit(0)
    if len(sys.argv) > 3 and sys.argv[1] == 'skip':  # свідомо без відповіді (троль/спам/рос. образи) — з причиною
        d = json.load(open(SKIP)) if os.path.exists(SKIP) else {}
        d[sys.argv[2]] = sys.argv[3]; json.dump(d, open(SKIP, 'w'), ensure_ascii=False, indent=1); print('skip', sys.argv[2]); sys.exit(0)
    u = unanswered()
    for x in u: print('UNANSWERED', *x[:3], '|', x[3], '|', x[4])
    print('unanswered:', len(u)); sys.exit(1 if u else 0)
