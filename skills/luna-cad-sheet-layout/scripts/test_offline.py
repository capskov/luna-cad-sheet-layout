"""Offline behavioral checks: does not connect to or mutate AutoCAD."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pythoncom
import cad_session as cad


class Contracts(unittest.TestCase):
    def session(self):
        s = cad.Session.__new__(cad.Session)
        s.read_only = False
        s.doc = object()
        s.settle = lambda: None
        return s

    def test_absolute_target_required_before_com(self):
        with self.assertRaises(ValueError):
            cad.Session('relative.dwg', Path.cwd())

    def test_readonly_mutation_rejected(self):
        s = self.session()
        s.read_only = True
        with self.assertRaises(RuntimeError):
            s.save()
        with self.assertRaises(RuntimeError):
            s.select_layout('x')

    def test_a3_window_before_plot_type_and_exact_scale(self):
        s = self.session()
        layout = object()
        s.select_layout = lambda _: layout
        s.paper = lambda: None
        log = []
        def call(obj, name, *args):
            log.append((obj, name, args))
        def put(obj, name, value):
            log.append((obj, name, (value,)))
        with patch.object(cad, 'call', call), patch.object(cad, 'put', put):
            s.configure_a3('x')
        names = [x[1] for x in log]
        self.assertLess(names.index('SetWindowToPlot'), names.index('PlotType'))
        self.assertIn((layout, 'UseStandardScale', (False,)), log)
        self.assertIn((layout, 'SetCustomScale', (1.0, 1.0)), log)
        self.assertTrue(all(obj is layout for obj, _, _ in log))

    def test_overall_viewport_never_unlocked(self):
        s = self.session()
        s.select_layout = lambda _: object()
        s.viewport = lambda *_: object()
        s.viewport_numbers = lambda _: {'A': 1}
        with patch.object(cad, 'put') as setter:
            with self.assertRaises(RuntimeError):
                s.activate('x', 'A')
            setter.assert_not_called()

    def test_nonbusy_hresult_is_not_retried(self):
        calls = []
        def fail():
            calls.append(1)
            raise pythoncom.com_error(-2147024809, 'bad argument', None, None)
        with self.assertRaises(pythoncom.com_error):
            cad.retry(fail, 'test')
        self.assertEqual(len(calls), 1)

    def test_existing_pdf_never_overwritten(self):
        s = self.session()
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'already.pdf'
            p.write_bytes(b'keep')
            with self.assertRaises(ValueError):
                s.plot('x', p)
            self.assertEqual(p.read_bytes(), b'keep')

    def test_busy_retries_are_bounded(self):
        calls = []
        def fail():
            calls.append(1)
            raise pythoncom.com_error(-2147418111, 'busy', None, None)
        with patch.object(cad.time, 'sleep'), patch('builtins.print'):
            with self.assertRaises(pythoncom.com_error):
                cad.retry(fail, 'busy-contract')
        self.assertEqual(len(calls), 31)

    def test_plot_cleanup_preserves_primary_error(self):
        s = self.session()
        s.paper = lambda: None
        s.var = lambda _: 2
        lay, plotter = object(), object()
        def getter(obj, name):
            return {'ActiveLayout': lay, 'Name': 'x', 'Plot': plotter}[name]
        def caller(obj, name, *args):
            if name == 'PlotToFile':
                raise ValueError('primary plot failure')
            if name == 'SetVariable' and args[-1] == 2:
                raise RuntimeError('secondary restoration failure')
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cad, 'get', getter), patch.object(cad, 'call', caller), patch('builtins.print'):
                with self.assertRaisesRegex(ValueError, 'primary plot failure'):
                    s.plot('x', Path(directory)/'new.pdf')


if __name__ == '__main__':
    unittest.main(verbosity=2)
