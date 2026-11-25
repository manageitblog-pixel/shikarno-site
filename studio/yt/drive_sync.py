"""Резерв студії в Google Drive власника (власник 25.11: «відразу заливай десь»; «артефакти, важливі документи, воркфлоу —
усе теж завантажуй і гарно по папках розкладай»). Окремий OAuth зі scope drive.file (yt/drive_token.json) — лише файли студії.
Структура в Drive «ШІкарно студія/»:
  Відео й озвучка/<slug>/…   ← /home/claude/eps/<slug>/* (mp4, wav, opus, png, jpg, srt, json)
  Документи/…                ← docs/** (md)
  Воркфлоу/GitHub Actions/…  ← .github/workflows/*.yml;  Воркфлоу/<файл> ← знімок розкладу задач
  Артефакти/HQ-дашборд/…     ← studio/hq/index.html, data.json, asks.json
  Дані/…                     ← studio/data/*.sqlite, ops_dump.sql, snapshot/*
Секретів НЕ заливаємо (token/.key/client_secret/«Доступи» — відсікаються фільтром).
Індекс (ключ → fileId, md5) — studio/data/drive_index.json (у git, без секретів). Ключі: «claude:<шлях від /home/claude>» або «repo:<шлях від кореня репо>».
  python3 drive_sync.py push <файл|тека> [...]    → залити нові/змінені
  python3 drive_sync.py all                        → документи + воркфлоу + артефакти + дані + усі eps/<slug>
  python3 drive_sync.py restore [префікс-ключа]    → стягнути відсутні локально (напр. restore claude:eps/ep88)
  python3 drive_sync.py status"""
import hashlib, json, os, sys, urllib.request, urllib.parse
sys.path.insert(0, '/home/claude/yt'); import yt
H = os.path.realpath('/home/claude')
REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'))
IDX = os.path.join(REPO, 'studio', 'data', 'drive_index.json')
ROOT_NAME = 'ШІкарно студія'
MEDIA_EXT = ('.mp4', '.wav', '.opus', '.png', '.jpg', '.jpeg', '.srt', '.json', '.mp3', '.m4a')
SECRET = ('token', '.key', 'client_secret', '.pkce', 'secret', 'credential', '.env')
API = 'https://www.googleapis.com/drive/v3'


def idx():
    d = json.load(open(IDX)) if os.path.exists(IDX) else {}
    d.setdefault('files', {}); d.setdefault('folders', {})
    if d.get('folder') and '' not in d['folders']: d['folders'][''] = d.pop('folder')
    d.pop('folder', None)
    for k in [k for k in d['files'] if ':' not in k]:  # міграція старих ключів (25.11, плаский варіант)
        d['files']['claude:' + k] = d['files'].pop(k)
    return d


def save(d):
    json.dump(d, open(IDX, 'w'), ensure_ascii=False, indent=1, sort_keys=True)


def req(url, data=None, method=None, ctype='application/json'):
    h = {'Authorization': 'Bearer ' + yt.token('drive_token.json')}
    if data is not None: h['Content-Type'] = ctype
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=600)


def folder(d, path):
    """Тека за шляхом «Відео й озвучка/ep88» (створює ланцюжок)."""
    if path in d['folders']: return d['folders'][path]
    parent = folder(d, os.path.dirname(path)) if path else None
    name = os.path.basename(path) if path else ROOT_NAME
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent: meta['parents'] = [parent]
    d['folders'][path] = json.load(req(API + '/files', json.dumps(meta).encode()))['id']; save(d)
    return d['folders'][path]


def key_of(p):
    rp = os.path.realpath(p)
    if rp.startswith(REPO + os.sep): return 'repo:' + os.path.relpath(rp, REPO)
    if rp.startswith(H + os.sep): return 'claude:' + os.path.relpath(rp, H)
    raise ValueError('поза студією: ' + p)


def local_of(k):
    src, rel = k.split(':', 1)
    return os.path.join(REPO if src == 'repo' else H, rel)


def drive_dir(k):
    src, rel = k.split(':', 1); dn = os.path.dirname(rel)
    if src == 'claude' and rel.startswith('eps/'): return 'Відео й озвучка/' + dn[4:] if dn != 'eps' else 'Відео й озвучка'
    if src == 'repo' and rel.startswith('studio/eps/') and '/' in rel[11:]:  # симлінк eps → studio/eps (_vo_backup тощо)
        return 'Відео й озвучка/' + os.path.dirname(rel[11:])
    if src == 'repo' and rel.startswith('docs/'): return ('Документи/' + dn[5:]).rstrip('/') if dn != 'docs' else 'Документи'
    if src == 'repo' and rel.startswith('.github/workflows/'): return 'Воркфлоу/GitHub Actions'
    if src == 'repo' and rel.startswith('studio/hq/'): return 'Артефакти/HQ-дашборд'
    if src == 'repo' and rel.startswith('studio/data/'): return ('Дані/' + dn[12:]).rstrip('/') if dn != 'studio/data' else 'Дані'
    if src == 'claude' and rel.startswith('workflow/'): return 'Воркфлоу'
    return 'Інше/' + dn


def md5(p):
    m = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): m.update(b)
    return m.hexdigest()


def upload(p, d):
    k = key_of(p); h = md5(p); old = d['files'].get(k); want = drive_dir(k)
    if old and old['md5'] == h and old.get('dir') == want: return None
    par = folder(d, want)
    if old and old['md5'] == h:  # той самий вміст — лише перенести в правильну теку
        q = urllib.parse.urlencode({'addParents': par, 'removeParents': old.get('parent') or d['folders'].get('', ''), 'fields': 'id'})
        req(f"{API}/files/{old['id']}?{q}", json.dumps({'name': os.path.basename(p)}).encode(), 'PATCH')
        old.update(dir=want, parent=par); save(d); return k
    meta = {'name': os.path.basename(p)}
    if old:
        url = f"https://www.googleapis.com/upload/drive/v3/files/{old['id']}?uploadType=resumable"; method = 'PATCH'
    else:
        meta['parents'] = [par]; url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable'; method = 'POST'
    loc = req(url, json.dumps(meta).encode(), method).headers['Location']
    with open(p, 'rb') as f:
        fid = json.load(req(loc, f.read(), 'PUT', 'application/octet-stream'))['id']
    d['files'][k] = {'id': fid, 'md5': h, 'size': os.path.getsize(p), 'dir': want, 'parent': (old or {}).get('parent', par)}
    save(d); return k


def ok(p):
    b = os.path.basename(p).lower()
    if any(s in b for s in SECRET) or os.path.getsize(p) == 0 or b.endswith('.lock'): return False
    k = key_of(p)
    if k.startswith('claude:eps/'): return b.endswith(MEDIA_EXT)
    return True


def push(paths):
    d = idx(); n = 0
    for a in paths:
        if not os.path.exists(a): continue
        it = [os.path.join(r, f) for r, ds, fs in os.walk(a) for f in fs if '/.' not in r and '__pycache__' not in r] if os.path.isdir(a) else [a]
        for p in sorted(it):
            try:
                if ok(p) and upload(p, d): n += 1; print('up', key_of(p))
            except ValueError: pass
    print('pushed', n)


def all_paths():
    ps = [os.path.join(REPO, x) for x in ('docs', '.github/workflows', 'studio/hq/index.html', 'studio/hq/data.json', 'studio/hq/asks.json',
                                          'studio/data/analytics.sqlite', 'studio/data/ops.sqlite', 'studio/data/ops_dump.sql', 'studio/data/snapshot')]
    ps.append(os.path.join(H, 'workflow'))
    eps = os.path.join(H, 'eps')
    ps += [os.path.join(eps, s) for s in sorted(os.listdir(eps)) if os.path.isdir(os.path.join(eps, s)) and not s.startswith(('_', '.'))]
    return ps


def restore(prefix=''):
    d = idx(); n = 0
    for k, m in d['files'].items():
        dst = local_of(k)
        if not k.startswith(prefix) or os.path.exists(dst): continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f: f.write(req(f"{API}/files/{m['id']}?alt=media").read())
        n += 1
    print('restored', n)


if __name__ == '__main__':
    a = sys.argv[1:] or ['status']
    if a[0] == 'push': push(a[1:])
    elif a[0] == 'all': push(all_paths())
    elif a[0] == 'restore': restore(a[1] if len(a) > 1 else '')
    else:
        d = idx(); print('files', len(d['files']), 'MB', round(sum(x['size'] for x in d['files'].values()) / 1e6, 1), 'folders', len(d['folders']))
