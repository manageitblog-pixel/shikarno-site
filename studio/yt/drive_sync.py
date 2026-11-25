"""Резерв медіа студії в Google Drive власника (власник 25.11: «відразу заливай десь, щоб воно там були»).
Scope drive.file — лише файли, створені цим застосунком; папка «ШІкарно студія». Індекс (шлях → fileId, md5) — studio/data/drive_index.json (у git, без секретів).
  python3 drive_sync.py push <файл|тека> [...]   → залити нові/змінені (mp4, wav, opus, png, jpg, sqlite, json)
  python3 drive_sync.py restore [префікс]          → стягнути відсутні локально файли з індексу
  python3 drive_sync.py status                     → скільки файлів і МБ у резерві
Шляхи в індексі — відносно /home/claude (напр. eps/ep88/short.mp4)."""
import hashlib, json, os, sys, urllib.request, urllib.parse
sys.path.insert(0, '/home/claude/yt'); import yt
H = '/home/claude'
IDX = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'drive_index.json')
EXT = ('.mp4', '.wav', '.opus', '.png', '.jpg', '.jpeg', '.sqlite', '.json', '.srt')
API = 'https://www.googleapis.com/drive/v3'


def idx():
    return json.load(open(IDX)) if os.path.exists(IDX) else {'folder': None, 'files': {}}


def save(d):
    json.dump(d, open(IDX, 'w'), ensure_ascii=False, indent=1, sort_keys=True)


def req(url, data=None, method=None, ctype='application/json'):
    h = {'Authorization': 'Bearer ' + yt.token('drive_token.json')}
    if data is not None: h['Content-Type'] = ctype
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    return urllib.request.urlopen(r, timeout=600)


def folder(d):
    if d.get('folder'): return d['folder']
    body = json.dumps({'name': 'ШІкарно студія', 'mimeType': 'application/vnd.google-apps.folder'}).encode()
    d['folder'] = json.load(req(API + '/files', body))['id']; save(d); return d['folder']


def md5(p):
    m = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): m.update(b)
    return m.hexdigest()


def upload(p, d):
    rel = os.path.relpath(os.path.realpath(p), os.path.realpath(H)) if os.path.realpath(p).startswith(os.path.realpath(H)) else os.path.relpath(p, H)
    h = md5(p); old = d['files'].get(rel)
    if old and old['md5'] == h: return None
    size = os.path.getsize(p)
    meta = {'name': rel.replace('/', '__')}
    if old:  # оновити вміст того ж файлу
        url = f"https://www.googleapis.com/upload/drive/v3/files/{old['id']}?uploadType=resumable"; method = 'PATCH'
    else:
        meta['parents'] = [folder(d)]; url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable'; method = 'POST'
    r = req(url, json.dumps(meta).encode(), method)
    loc = r.headers['Location']
    with open(p, 'rb') as f:
        fid = json.load(req(loc, f.read(), 'PUT', 'application/octet-stream'))['id']
    d['files'][rel] = {'id': fid, 'md5': h, 'size': size}; save(d)
    return rel


def push(paths):
    d = idx(); n = 0
    for a in paths:
        it = [os.path.join(r, f) for r, _, fs in os.walk(a) for f in fs] if os.path.isdir(a) else [a]
        for p in it:
            if p.endswith(EXT) and os.path.getsize(p) > 0 and upload(p, d): n += 1; print('up', p)
    print('pushed', n)


def restore(prefix=''):
    d = idx(); n = 0
    for rel, m in d['files'].items():
        dst = os.path.join(H, rel)
        if not rel.startswith(prefix) or os.path.exists(dst): continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'wb') as f: f.write(req(f"{API}/files/{m['id']}?alt=media").read())
        n += 1
    print('restored', n)


if __name__ == '__main__':
    a = sys.argv[1:] or ['status']
    if a[0] == 'push': push(a[1:])
    elif a[0] == 'restore': restore(a[1] if len(a) > 1 else '')
    else:
        d = idx(); print('files', len(d['files']), 'MB', round(sum(x['size'] for x in d['files'].values()) / 1e6, 1))
