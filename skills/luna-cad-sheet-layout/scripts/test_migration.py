"""Focused migration checks; no AutoCAD connection or writes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cad_session as cad
from frame_candidates import candidates, date_clues


class Migration(unittest.TestCase):
    def test_filename_dates_not_mtime_choose_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'frame_20261016.dwg').write_bytes(b'new')
            (root / 'frame_2026-09-28.dwg').write_bytes(b'old')
            (root / 'not-a-frame.txt').write_text('ignored')
            report = candidates(root, with_hash=True)
            self.assertIsNone(report['selected'])
            self.assertEqual(len(report['candidates']), 2)
            self.assertEqual({tuple(x['filename_dates']) for x in report['candidates']},
                             {('2026-10-16',), ('2026-09-28',)})
            self.assertTrue(all(len(x['sha256']) == 64 for x in report['candidates']))
            self.assertEqual((root / 'frame_20261016.dwg').read_bytes(), b'new')

    def test_invalid_dates_do_not_become_revisions(self):
        self.assertEqual(date_clues('frame_20260230_20261301'), [])
        self.assertEqual(date_clues('frame_2026年10月16日'), ['2026-10-16'])

    def test_unsupported_progid_rejected_before_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'test.dwg'
            target.write_bytes(b'fixture')
            with patch.object(cad.win32com.client, 'GetActiveObject') as connect:
                with self.assertRaises(ValueError):
                    cad.Session(target, root, progid='AutoCAD.Application')
                connect.assert_not_called()

    def test_selected_version_and_inspection_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'test.dwg'
            target.write_bytes(b'fixture')
            app, docs, doc = object(), object(), object()
            def getter(obj, name):
                return {'Documents': docs, 'Count': 1, 'FullName': str(target), 'ReadOnly': False}[name]
            with patch.object(cad.win32com.client, 'GetActiveObject', return_value=app) as connect, \
                 patch.object(cad, 'get', getter), patch.object(cad, 'call', return_value=doc), \
                 patch.object(cad.Session, 'idle'), patch.object(cad.Session, 'var', return_value=0):
                s = cad.Session(target, root, allow_read_only=True, progid='AutoCAD.Application.25.1')
                connect.assert_called_once_with('AutoCAD.Application.25.1')
                with self.assertRaises(RuntimeError):
                    s.save()

    def test_unsupported_view_rejected_before_unlock(self):
        s = cad.Session.__new__(cad.Session)
        s.layout = Mock(return_value=object())
        s.viewport = Mock(return_value=object())
        s.activate = Mock()
        with patch.object(cad, 'get', return_value=0.25), patch.object(cad, 'put') as setter:
            with self.assertRaises(RuntimeError):
                s.fit('sheet', 'A', [1.0, 2.0], 1.0)
            s.activate.assert_not_called()
            setter.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
