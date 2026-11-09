"""Behavioral tests run against isolated temporary brains, never real memories."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / 'agent-brain' / 'scripts' / 'brain.py'
INSTALL = REPO / 'agent-brain' / 'scripts' / 'install.py'


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.scratch = (REPO / '.test-tmp').resolve()
        self.scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.scratch)
        self.base = Path(self.temp.name)
        self.root = self.base / 'private-brain'

    def tearDown(self):
        self.assertEqual(self.base.resolve().parent, self.scratch)
        self.temp.cleanup()

    def run_cli(self, *args, ok=True, env=None):
        p = subprocess.run([sys.executable, str(CLI), '--root', str(self.root), *args],
                           text=True, capture_output=True, env=env)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0)
        return p

    def init(self):
        self.run_cli('init')

    def body(self, text='Outcome: saved work.\nEvidence: observed locally.\nNext: resume.\n'):
        p = self.base / 'body.md'
        p.write_text(text, encoding='utf-8')
        return p

    def capture(self, agent='worker', project='lantern'):
        return self.run_cli('capture', '--project', project, '--harness', 'codex',
                            '--agent', agent, '--source', 'test-session',
                            '--body-file', str(self.base / 'body.md'))

    def test_init_is_idempotent_and_preserves_user_edits(self):
        self.init()
        p = self.root / 'profile.md'
        p.write_text('A user-owned fact.\n', encoding='utf-8')
        self.init()
        self.assertEqual(p.read_text(encoding='utf-8'), 'A user-owned fact.\n')
        self.assertFalse((self.root / '.git').exists())

    def test_init_refuses_to_adopt_nonempty_unrelated_folder(self):
        self.root.mkdir()
        (self.root / 'unrelated.md').write_text('Keep me', encoding='utf-8')
        self.run_cli('init', ok=False)
        self.assertFalse((self.root / 'brain.json').exists())

    def test_concurrent_workers_keep_every_contribution(self):
        self.init()
        self.body()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda n: self.capture(f'worker-{n}'), range(16)))
        paths = [json.loads(p.stdout)['path'] for p in results]
        self.assertEqual(len(set(paths)), 16)
        self.assertEqual(len(list((self.root / 'inbox' / 'lantern').glob('*.md'))), 16)
        for rel in paths:
            self.assertIn('status: "pending"', (self.root / rel).read_text(encoding='utf-8'))

    def test_publish_refuses_stale_revision(self):
        self.init()
        rev = json.loads(self.run_cli('read', 'profile.md').stdout)['sha256']
        first = self.body('User confirmed: short responses.\n')
        self.run_cli('publish', 'profile.md', '--expected-sha', rev,
                     '--body-file', str(first))
        second = self.body('User confirmed: long responses.\n')
        self.run_cli('publish', 'profile.md', '--expected-sha', rev,
                     '--body-file', str(second), ok=False)
        self.assertIn('short responses', (self.root / 'profile.md').read_text(encoding='utf-8'))

    def test_two_curators_cannot_overwrite_same_revision(self):
        self.init()
        rev = json.loads(self.run_cli('read', 'profile.md').stdout)['sha256']
        body = self.body()
        def attempt(n):
            return subprocess.run([sys.executable, str(CLI), '--root', str(self.root),
                'publish', 'profile.md', '--expected-sha', rev, '--body-file', str(body)],
                text=True, capture_output=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(sorted(p.returncode == 0 for p in results), [False, True])

    def test_path_escape_and_immutable_inbox_are_rejected(self):
        self.init()
        body = self.body()
        self.run_cli('read', '../outside.md', ok=False)
        self.run_cli('publish', '../outside.md', '--expected-sha', 'missing',
                     '--body-file', str(body), ok=False)
        self.run_cli('publish', 'inbox/lantern/replace.md', '--expected-sha', 'missing',
                     '--body-file', str(body), ok=False)
        self.run_cli('capture', '--project', '../outside', '--harness', 'codex',
                     '--agent', 'worker', '--source', 'test', '--body-file', str(body), ok=False)

    def test_symlink_escape_is_rejected_when_supported(self):
        self.init()
        outside = self.base / 'outside'
        outside.mkdir()
        try:
            (self.root / 'projects' / 'escape').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('OS does not permit symlink creation for this user')
        self.run_cli('publish', 'projects/escape/overview.md', '--expected-sha', 'missing',
                     '--body-file', str(self.body()), ok=False)
        self.assertFalse((outside / 'overview.md').exists())

    def test_reads_are_bounded_and_pending_search_is_opt_in(self):
        self.init()
        self.body('unique-pending-word\n' + 'x' * 10000)
        self.capture()
        default = json.loads(self.run_cli('search', 'unique-pending-word').stdout)
        self.assertEqual(default, [])
        pending = json.loads(self.run_cli('search', 'unique-pending-word', '--include-pending').stdout)
        self.assertEqual(len(pending), 1)
        rel = pending[0]['path']
        note = json.loads(self.run_cli('read', rel, '--max-chars', '250').stdout)
        self.assertLessEqual(len(note['content']), 250)
        self.assertTrue(note['truncated'])

    def test_install_preserves_unrelated_global_guidance_and_shares_one_root(self):
        self.init()
        home = self.base / 'fake-home'
        rules = home / '.codex' / 'AGENTS.md'
        rules.parent.mkdir(parents=True)
        rules.write_text('Keep existing guidance.\n', encoding='utf-8')
        command = [sys.executable, str(INSTALL), '--brain', str(self.root),
                   '--home', str(home), '--bootstrap', 'codex', 'opencode']
        for _ in range(2):
            p = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        installed = home / '.agents' / 'skills' / 'agent-brain'
        self.assertTrue((installed / 'SKILL.md').is_file())
        settings = json.loads((installed / 'brain.local.json').read_text(encoding='utf-8'))
        self.assertEqual(Path(settings['root']), self.root.resolve())
        text = rules.read_text(encoding='utf-8')
        self.assertTrue(text.startswith('Keep existing guidance.\n'))
        self.assertEqual(text.count('<!-- agent-brain:start -->'), 1)
        self.assertIn(str(self.root.resolve()), text)
        self.assertTrue((home / '.config' / 'opencode' / 'AGENTS.md').is_file())
        self.assertFalse((home / '.claude' / 'CLAUDE.md').exists())


if __name__ == '__main__':
    unittest.main()
