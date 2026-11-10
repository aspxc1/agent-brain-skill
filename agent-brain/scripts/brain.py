#!/usr/bin/env python3
"""Local Markdown memory operations. Python 3.10+, standard library only."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import sys
import time
import uuid

SKILL = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
CANONICAL = re.compile(r'^(profile\.md|practices\.md|mistakes\.md|projects/[a-z0-9]+(?:-[a-z0-9]+)*/overview\.md)$')
MAX_BODY = 100_000


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def root_path(explicit=None):
    value = explicit or os.environ.get('AGENT_BRAIN_ROOT')
    if not value:
        local = SKILL / 'brain.local.json'
        if local.is_file():
            value = json.loads(local.read_text(encoding='utf-8'))['root']
    if not value:
        raise ValueError('No brain configured. Pass --root, set AGENT_BRAIN_ROOT, or run install.py.')
    return Path(value).expanduser().resolve()


def confined(root, relative):
    # Reject drive paths, traversal and alternate Windows path separators up front.
    rel = PurePosixPath(relative)
    if not relative or '\\' in relative or ':' in relative or rel.is_absolute() or '..' in rel.parts:
        raise ValueError('Use a relative path inside the brain.')
    path = (root / Path(*rel.parts)).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError(f'Path escapes the brain root: {relative!r} resolved to {path}, root {root}.')
    return path


def require_brain(root):
    marker = confined(root, 'brain.json')
    if not marker.is_file():
        raise ValueError('Not an initialized brain. Run init with the intended --root.')
    if json.loads(marker.read_text(encoding='utf-8')).get('schema_version') != 1:
        raise ValueError('Unsupported brain schema; do not rewrite this brain.')


@contextmanager
def writer_lock(root, timeout=10):
    # root is already resolved. Resolving this volatile directory on Windows can
    # race another writer's rmdir and return an extended-path alias (or hold a
    # deletion-pending handle). mkdir itself rejects existing links and files.
    lock = root / '.brain.lock'
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir()
            break
        except OSError as error:
            # Windows may report access denied while the previous directory's
            # deletion finishes, rather than reporting that the lock exists.
            busy = isinstance(error, FileExistsError) or (
                os.name == 'nt' and getattr(error, 'winerror', None) in (5, 32))
            if not busy:
                raise
            if time.monotonic() >= deadline:
                raise ValueError('Cannot acquire brain lock. Inspect permissions and .brain.lock/owner.json; never steal a live lock.') from error
            time.sleep(0.03)
    try:
        (lock / 'owner.json').write_text(json.dumps({
            'pid': os.getpid(), 'host': socket.gethostname(), 'acquired_at': now()
        }), encoding='utf-8')
        yield
    finally:
        owner = lock / 'owner.json'
        if owner.exists():
            owner.unlink()
        lock.rmdir()


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x', encoding='utf-8', newline='\n') as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def body_from(path):
    p = Path(path)
    if p.stat().st_size > MAX_BODY * 4:
        raise ValueError('Memory is too large; summarize it before saving.')
    text = p.read_text(encoding='utf-8').strip()
    if not text or len(text) > MAX_BODY:
        raise ValueError('Memory body must contain 1-100000 characters.')
    return text + '\n'


def initialize(root):
    if root.exists() and any(root.iterdir()):
        require_brain(root)
        return {'root': str(root), 'created': False}
    root.mkdir(parents=True, exist_ok=True)
    # Initialized once by a coordinator, before starting workers.
    for name in ('projects', 'inbox', 'archive'):
        (root / name).mkdir(exist_ok=True)
    for source in (SKILL / 'assets' / 'vault').iterdir():
        if source.is_file():
            target = confined(root, source.name)
            with target.open('x', encoding='utf-8', newline='\n') as out:
                out.write(source.read_text(encoding='utf-8'))
    with (root / 'brain.json').open('x', encoding='utf-8') as out:
        json.dump({'schema_version': 1, 'brain_id': uuid.uuid4().hex,
                   'created_at': now(), 'storage': 'local-markdown'}, out, indent=2)
        out.write('\n')
    return {'root': str(root), 'created': True}


def capture(root, args):
    if not SLUG.fullmatch(args.project) or len(args.project) > 80:
        raise ValueError('Project must be a lowercase hyphen-separated slug, at most 80 characters.')
    for value in (args.harness, args.agent, args.source):
        if not value.strip() or len(value) > 500:
            raise ValueError('Harness, agent, and source must be nonempty and at most 500 characters.')
    body = body_from(args.body_file)
    note_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex
    rel = f'inbox/{args.project}/{note_id}.md'
    metadata = {'id': note_id, 'kind': args.kind, 'project': args.project,
                'created_at': now(), 'harness': args.harness, 'agent': args.agent,
                'source': args.source, 'evidence': args.evidence, 'status': 'pending'}
    front = '\n'.join(k + ': ' + json.dumps(v, ensure_ascii=False) for k, v in metadata.items())
    with writer_lock(root):
        path = confined(root, rel)
        if path.exists():
            raise ValueError('Contribution already exists; refusing replacement.')
        atomic_write(path, '---\n' + front + '\n---\n\n' + body)
    return {'path': rel, 'id': note_id, 'status': 'pending'}


def read_note(root, relative, max_chars):
    path = confined(root, relative)
    if path.suffix != '.md':
        raise ValueError('Only Markdown memory notes may be read.')
    data = path.read_bytes()
    text = data.decode('utf-8-sig')
    return {'path': relative, 'sha256': digest(data), 'content': text[:max_chars],
            'truncated': len(text) > max_chars}


def publish(root, args):
    if not CANONICAL.fullmatch(args.target):
        raise ValueError('Publish only profile.md, practices.md, mistakes.md, or projects/<slug>/overview.md.')
    body = body_from(args.body_file)
    if args.expected_sha != 'missing' and not re.fullmatch(r'[0-9a-f]{64}', args.expected_sha):
        raise ValueError('Expected SHA must be the read command hash, or missing for a new note.')
    with writer_lock(root):
        path = confined(root, args.target)
        current = digest(path.read_bytes()) if path.exists() else 'missing'
        if current != args.expected_sha:
            raise ValueError('Revision conflict. Reread the latest note and merge before publishing.')
        atomic_write(path, body)
    return {'path': args.target, 'sha256': digest(body.encode('utf-8'))}


def search(root, args):
    terms = args.query.casefold().split()
    candidates = [root / 'profile.md', root / 'practices.md', root / 'mistakes.md']
    candidates += sorted((root / 'projects').glob('*/overview.md'))
    if args.include_pending:
        candidates += sorted((root / 'inbox').glob('*/*.md'), reverse=True)
    matches = []
    for path in candidates:
        rel = path.relative_to(root).as_posix()
        if args.project and rel.startswith(('projects/', 'inbox/')) and rel.split('/')[1] != args.project:
            continue
        path = confined(root, rel)
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8-sig')
        haystack = (rel + '\n' + text).casefold()
        if all(term in haystack for term in terms):
            excerpt = next((line for line in text.splitlines()
                            if any(term in line.casefold() for term in terms)), '')
            matches.append({'path': rel, 'excerpt': excerpt[:240],
                            'pending': rel.startswith('inbox/')})
        if len(matches) >= args.limit:
            break
    return matches


def positive_bound(value):
    number = int(value)
    if not 1 <= number <= 100000:
        raise argparse.ArgumentTypeError('Use an integer from 1 to 100000.')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', help='Explicit local brain root; overrides environment and local config.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init', help='Create an empty brain without overwriting existing notes.')
    sub.add_parser('status', help='Show note counts, configured root, and lock presence.')
    read = sub.add_parser('read', help='Read a note and its revision hash.')
    read.add_argument('path')
    read.add_argument('--max-chars', type=positive_bound, default=12000)
    find = sub.add_parser('search', help='Search curated notes; pending contributions are opt-in.')
    find.add_argument('query')
    find.add_argument('--project')
    find.add_argument('--include-pending', action='store_true')
    find.add_argument('--limit', type=positive_bound, default=8)
    note = sub.add_parser('capture', help='Create a uniquely named immutable pending contribution.')
    for field in ('project', 'harness', 'agent', 'source', 'body-file'):
        note.add_argument('--' + field, required=True)
    note.add_argument('--kind', choices=('session', 'decision', 'preference', 'practice', 'mistake', 'handoff'), default='session')
    note.add_argument('--evidence', choices=('reported', 'observed', 'user-confirmed'), default='reported')
    put = sub.add_parser('publish', help='Curator: compare revision and atomically publish one canonical note.')
    put.add_argument('target')
    put.add_argument('--expected-sha', required=True)
    put.add_argument('--body-file', required=True)
    args = parser.parse_args()
    try:
        root = root_path(args.root)
        if args.command == 'init':
            result = initialize(root)
        else:
            require_brain(root)
            if args.command == 'read':
                result = read_note(root, args.path, args.max_chars)
            elif args.command == 'search':
                result = search(root, args)
            elif args.command == 'capture':
                result = capture(root, args)
            elif args.command == 'publish':
                result = publish(root, args)
            else:
                result = {'root': str(root), 'locked': (root / '.brain.lock').exists(),
                          'brain_id': json.loads(confined(root, 'brain.json').read_text(encoding='utf-8'))['brain_id'],
                          'projects': len(list((root / 'projects').glob('*/overview.md'))),
                          'contributions': len(list((root / 'inbox').glob('*/*.md')))}
        # ASCII-safe JSON survives Windows code pages; json.loads restores Unicode.
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print('agent-brain: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
